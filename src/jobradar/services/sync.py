from datetime import UTC, datetime

import httpx

from jobradar.adapters.arbeitnow import fetch_arbeitnow_jobs
from jobradar.adapters.arbeitsagentur import fetch_arbeitsagentur_jobs
from jobradar.schemas.job import JobPreviewResponse
from jobradar.services.cache import load_cached_jobs, save_cached_jobs

MAX_JOB_DOWNLOAD_LIMIT = 25


def preview_jobs(
    *,
    limit: int,
    remote_only: bool = False,
    location: str | None = None,
    radius_km: int | None = None,
) -> JobPreviewResponse:
    limit = min(limit, MAX_JOB_DOWNLOAD_LIMIT)
    jobs = []
    failures: list[httpx.HTTPError] = []
    for fetcher in (
        lambda: fetch_arbeitsagentur_jobs(
            limit=limit,
            remote_only=remote_only,
            location=location,
            radius_km=radius_km,
        ),
        lambda: fetch_arbeitnow_jobs(limit=limit, remote_only=remote_only),
    ):
        try:
            jobs.extend(fetcher())
        except httpx.HTTPError as exc:
            failures.append(exc)

    if jobs or not failures:
        save_cached_jobs(jobs)
    else:
        cached_jobs = load_cached_jobs()
        if cached_jobs is None:
            raise failures[0]
        jobs = [job for job in cached_jobs if not remote_only or job.remote]
        return JobPreviewResponse(
            source="cache",
            count=min(len(jobs), limit),
            jobs=jobs[:limit],
        )

    jobs.sort(
        key=lambda job: job.posted_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return JobPreviewResponse(
        source="multiple",
        count=min(len(jobs), limit),
        jobs=jobs[:limit],
    )
