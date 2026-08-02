from typing import Annotated

import httpx
from fastapi import APIRouter, HTTPException, Query

from jobradar.schemas.job import JobPreviewResponse
from jobradar.services.sync import preview_jobs

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("/preview")
def read_jobs_preview(
    location: Annotated[
        str,
        Query(min_length=2, max_length=80, description="German city or postcode"),
    ],
    radius_km: Annotated[
        int,
        Query(ge=5, le=500, description="Search radius in kilometres"),
    ] = 50,
    limit: Annotated[
        int,
        Query(ge=1, le=25, description="Maximum number of jobs to return"),
    ] = 10,
    remote_only: Annotated[
        bool,
        Query(description="Return only jobs marked as remote by the provider"),
    ] = False,
) -> JobPreviewResponse:
    try:
        return preview_jobs(
            limit=limit,
            remote_only=remote_only,
            location=location,
            radius_km=radius_km,
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=502,
            detail="Failed to fetch jobs from the configured providers",
        ) from exc
