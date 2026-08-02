from jobradar.adapters.arbeitnow import ARBEITNOW_SOURCE, fetch_arbeitnow_jobs
from jobradar.schemas.job import JobPreviewResponse


def preview_jobs(*, limit: int, remote_only: bool = False) -> JobPreviewResponse:
    jobs = fetch_arbeitnow_jobs(limit=limit, remote_only=remote_only)
    return JobPreviewResponse(
        source=ARBEITNOW_SOURCE,
        count=len(jobs),
        jobs=jobs,
    )
