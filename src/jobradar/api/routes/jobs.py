from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query

from jobradar.schemas.job import JobPreviewResponse
from jobradar.services.sync import preview_jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/preview")
def read_jobs_preview(
    limit: Annotated[
        int,
        Query(ge=1, le=50, description="Maximum number of jobs to return"),
    ] = 10,
    remote_only: Annotated[
        bool,
        Query(description="Return only jobs marked as remote by the provider"),
    ] = False,
) -> JobPreviewResponse:
    try:
        return preview_jobs(limit=limit, remote_only=remote_only)
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch jobs from Arbeitnow",
        ) from exc
