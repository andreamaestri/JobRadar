from functools import lru_cache
from math import asin, cos, radians, sin, sqrt
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import HttpUrl

from jobradar.api.routes.jobs import router as jobs_router
from jobradar.schemas.job import Job
from jobradar.services.sync import preview_jobs

CITY_COORDINATES = {
    "berlin": (52.5200, 13.4050),
    "cologne": (50.9375, 6.9603),
    "frankfurt": (50.1109, 8.6821),
    "hamburg": (53.5511, 9.9937),
    "munich": (48.1351, 11.5820),
}
GEOCODING_API_URL = "https://geocoding-api.open-meteo.com/v1/search"
GEOCODING_COUNTRY_CODE = "DE"

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
        url=HttpUrl("https://www.arbeitnow.com/"),
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
        url=HttpUrl("https://www.arbeitnow.com/"),
        description_html="",
    ),
    Job(
        source="offline",
        source_id="sample-3",
        company="Good Company",
        title="Community & Partnerships Lead",
        location="Amsterdam · Hybrid",
        tags=["Community", "Growth"],
        url=HttpUrl("https://www.arbeitnow.com/"),
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
        result = preview_jobs(
            limit=50,
            remote_only=remote_only,
            location=location or None,
            radius_km=radius_km if location else None,
        )
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

    origin = _geocode_location(search) or CITY_COORDINATES.get(search)
    matches: list[Job] = []
    for job in filtered:
        job_location = (job.location or "").lower()
        if search in job_location:
            matches.append(job)
            continue
        if origin is None:
            continue
        job_coordinates = _geocode_location(job_location)
        if job_coordinates is None:
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


@lru_cache(maxsize=256)
def _search_locations(
    location: str,
) -> tuple[tuple[str, float, float, str, str], ...]:
    """Search place names using Open-Meteo, while keeping failures non-fatal."""
    if len(location) < 2 or "remote" in location.lower():
        return ()
    try:
        response = httpx.get(
            GEOCODING_API_URL,
            params={
                "name": location,
                "count": 6,
                "countryCode": GEOCODING_COUNTRY_CODE,
                "language": "en",
                "format": "json",
            },
            timeout=3.0,
        )
        response.raise_for_status()
        payload: Any = response.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []
        locations = []
        for result in results:
            if not isinstance(result, dict):
                continue
            name = result.get("name")
            latitude = result.get("latitude")
            longitude = result.get("longitude")
            if (
                not isinstance(name, str)
                or not isinstance(latitude, (int, float))
                or not isinstance(longitude, (int, float))
            ):
                continue
            locations.append(
                (
                    name,
                    float(latitude),
                    float(longitude),
                    str(result.get("admin1") or ""),
                    str(result.get("country") or ""),
                )
            )
        return tuple(locations)
    except (httpx.HTTPError, ValueError, TypeError):
        return ()


def _geocode_location(location: str) -> tuple[float, float] | None:
    results = _search_locations(location)
    if results:
        return results[0][1], results[0][2]
    return None


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


@app.get("/api/geocode", include_in_schema=False)
def geocode_suggestions(
    query: str = Query(default="", min_length=2, max_length=80),
) -> list[dict[str, str]]:
    suggestions = []
    for name, latitude, longitude, admin1, country in _search_locations(query):
        label = ", ".join(part for part in (name, admin1, country) if part)
        suggestions.append(
            {
                "label": label,
                "value": name,
                "latitude": str(latitude),
                "longitude": str(longitude),
            }
        )
    return suggestions


@app.get("/jobs/{job_id}")
def read_job(job_id: int):
    return {
        "job_id": job_id,
        "status": "tracking",
    }
