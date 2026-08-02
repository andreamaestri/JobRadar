from datetime import datetime, timezone
from typing import Any

import httpx

from jobradar.schemas.job import Job

ARBEITNOW_SOURCE = "arbeitnow"
ARBEITNOW_API_URL = "https://www.arbeitnow.com/api/job-board-api"


def fetch_arbeitnow_jobs(*, limit: int, remote_only: bool = False) -> list[Job]:
    response = httpx.get(ARBEITNOW_API_URL, timeout=15.0)
    response.raise_for_status()

    payload = response.json()
    raw_jobs = payload.get("data", [])

    jobs = [
        _normalize_arbeitnow_job(raw_job)
        for raw_job in raw_jobs
        if _include_job(raw_job, remote_only=remote_only)
    ]
    return jobs[:limit]


def _include_job(raw_job: dict[str, Any], *, remote_only: bool) -> bool:
    if not remote_only:
        return True
    return bool(raw_job.get("remote"))


def _normalize_arbeitnow_job(raw_job: dict[str, Any]) -> Job:
    created_at = raw_job.get("created_at")
    posted_at = None
    if isinstance(created_at, (int, float)):
        posted_at = datetime.fromtimestamp(created_at, tz=timezone.utc)

    return Job(
        source=ARBEITNOW_SOURCE,
        source_id=str(raw_job["slug"]),
        title=raw_job["title"],
        company=raw_job["company_name"],
        location=raw_job.get("location"),
        remote=bool(raw_job.get("remote")),
        url=raw_job["url"],
        description_html=raw_job.get("description", ""),
        tags=_coerce_string_list(raw_job.get("tags")),
        job_types=_coerce_string_list(raw_job.get("job_types")),
        posted_at=posted_at,
    )


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]
