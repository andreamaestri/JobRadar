from datetime import UTC, datetime

import httpx

from jobradar.adapters.arbeitnow import fetch_arbeitnow_jobs
from jobradar.adapters.arbeitsagentur import fetch_arbeitsagentur_jobs
from jobradar.schemas.job import JobPreviewResponse


def preview_jobs(
    *,
    limit: int,
    remote_only: bool = False,
    location: str | None = None,
    radius_km: int | None = None,
) -> JobPreviewResponse:
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

    if not jobs and failures:
        raise failures[0]

    jobs.sort(
        key=lambda job: job.posted_at or datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return JobPreviewResponse(
        source="multiple",
        count=min(len(jobs), limit),
        jobs=jobs[:limit],
    )
