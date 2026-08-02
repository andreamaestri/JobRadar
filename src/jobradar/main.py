from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jobradar.api.routes.jobs import router as jobs_router
from jobradar.schemas.job import Job
from jobradar.services.sync import preview_jobs

CITY_COORDINATES = {
    "amsterdam": (52.3676, 4.9041),
    "barcelona": (41.3874, 2.1686),
    "berlin": (52.5200, 13.4050),
    "cologne": (50.9375, 6.9603),
    "frankfurt": (50.1109, 8.6821),
    "hamburg": (53.5511, 9.9937),
    "london": (51.5074, -0.1278),
    "munich": (48.1351, 11.5820),
    "paris": (48.8566, 2.3522),
    "vienna": (48.2082, 16.3738),
    "zurich": (47.3769, 8.5417),
}

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

FALLBACK_JOBS = [
    Job(
        source="offline",
        source_id="sample-1",
        company="Northstar Studio",
        title="Senior Product Designer",
        location="Berlin · Hybrid",
        tags=["Design", "Full time"],
        url="https://www.arbeitnow.com/",
        description_html="",
    ),
    Job(
        source="offline",
        source_id="sample-2",
        company="Open Field Labs",
        title="Frontend Engineer",
        location="Remote · Europe",
        remote=True,
        tags=["Engineering", "TypeScript"],
        url="https://www.arbeitnow.com/",
        description_html="",
    ),
    Job(
        source="offline",
        source_id="sample-3",
        company="Good Company",
        title="Community & Partnerships Lead",
        location="Amsterdam · Hybrid",
        tags=["Community", "Growth"],
        url="https://www.arbeitnow.com/",
        description_html="",
    ),
]

app.include_router(jobs_router)


@app.get("/", include_in_schema=False)
def read_root(
    request: Request,
    remote_only: bool = Query(default=False),
    location: str = Query(default="", max_length=80),
    radius_km: int = Query(default=50, ge=5, le=500),
):
    offline = False
    try:
        result = preview_jobs(limit=50, remote_only=remote_only)
        all_jobs = result.jobs
    except httpx.HTTPError:
        all_jobs = FALLBACK_JOBS
        offline = True

    jobs = filter_jobs(
        all_jobs,
        location=location,
        radius_km=radius_km,
        remote_only=remote_only,
    )[:12]

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": "JobRadar",
            "jobs": jobs,
            "remote_only": remote_only,
            "location": location,
            "radius_km": radius_km,
            "offline": offline,
        },
    )


def filter_jobs(
    jobs: list[Job],
    *,
    location: str,
    radius_km: int,
    remote_only: bool,
) -> list[Job]:
    search = location.strip().lower()
    filtered = [job for job in jobs if not remote_only or job.remote]
    if not search:
        return filtered

    origin = CITY_COORDINATES.get(search)
    matches: list[Job] = []
    for job in filtered:
        job_location = (job.location or "").lower()
        if search in job_location:
            matches.append(job)
            continue
        if origin is None:
            continue
        job_coordinates = next(
            (
                coordinates
                for city, coordinates in CITY_COORDINATES.items()
                if city in job_location
            ),
            None,
        )
        if job_coordinates and _distance_km(origin, job_coordinates) <= radius_km:
            matches.append(job)
    return matches


def _distance_km(
    first: tuple[float, float], second: tuple[float, float]
) -> float:
    first_lat, first_lon = map(radians, first)
    second_lat, second_lon = map(radians, second)
    delta_lat = second_lat - first_lat
    delta_lon = second_lon - first_lon
    haversine = (
        sin(delta_lat / 2) ** 2
        + cos(first_lat) * cos(second_lat) * sin(delta_lon / 2) ** 2
    )
    return 6371 * 2 * asin(sqrt(haversine))


@app.get("/about")
def read_about():
    return {
        "app": "JobRadar",
        "purpose": "Help track job opportunities",
    }


@app.get("/jobs/{job_id}")
def read_job(job_id: int):
    return {
        "job_id": job_id,
        "status": "tracking",
    }
