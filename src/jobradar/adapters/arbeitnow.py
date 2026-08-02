from datetime import UTC, datetime
from html import unescape
from typing import Any

import httpx

from jobradar.schemas.job import Job

ARBEITNOW_SOURCE = "arbeitnow"
ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"
MAX_ARBEITNOW_PAGES = 5


def fetch_arbeitnow_jobs(*, limit: int, remote_only: bool = False) -> list[Job]:
    if limit <= 0:
        return []

    jobs: list[Job] = []
    page = 1
    while len(jobs) < limit and page <= MAX_ARBEITNOW_PAGES:
        response = httpx.get(
            ARBEITNOW_API_URL,
            params={"page": page},
            timeout=15.0,
        )
        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, dict):
            break

        raw_jobs = payload.get("data", [])
        if not isinstance(raw_jobs, list):
            break

        for raw_job in raw_jobs:
            if not isinstance(raw_job, dict) or not _include_job(
                raw_job, remote_only=remote_only
            ):
                continue
            try:
                jobs.append(_normalize_arbeitnow_job(raw_job))
            except (KeyError, TypeError, ValueError):
                continue
            if len(jobs) >= limit:
                return jobs

        links = payload.get("links")
        if not isinstance(links, dict) or not links.get("next"):
            break
        page += 1

    return jobs


def _include_job(raw_job: dict[str, Any], *, remote_only: bool) -> bool:
    if not remote_only:
        return True
    return bool(raw_job.get("remote"))


def _normalize_arbeitnow_job(raw_job: dict[str, Any]) -> Job:
    created_at = raw_job.get("created_at")
    posted_at = None
    if isinstance(created_at, (int, float)):
        posted_at = datetime.fromtimestamp(created_at, tz=UTC)

    description = raw_job.get("description", "")
    if not isinstance(description, str):
        description = str(description)
    if "&lt;" in description or "&gt;" in description:
        description = unescape(description)

    return Job(
        source=ARBEITNOW_SOURCE,
        source_id=str(raw_job["slug"]),
        title=raw_job["title"],
        company=raw_job["company_name"],
        location=raw_job.get("location"),
        remote=bool(raw_job.get("remote")),
        url=raw_job["url"],
        description_html=description,
        tags=_coerce_string_list(raw_job.get("tags")),
        job_types=_coerce_string_list(raw_job.get("job_types")),
        posted_at=posted_at,
    )


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
