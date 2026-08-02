import json
import os
import tempfile
from pathlib import Path
from typing import Any

from jobradar.schemas.job import Job

LocationResult = tuple[str, float, float, str, str]


def _cache_path() -> Path:
    configured_path = os.environ.get("JOBRADAR_CACHE_FILE")
    if configured_path:
        return Path(configured_path)
    return Path.cwd() / ".jobradar-cache.json"


def _read_cache() -> dict[str, Any]:
    try:
        with _cache_path().open(encoding="utf-8") as cache_file:
            payload = json.load(cache_file)
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _write_cache(payload: dict[str, Any]) -> None:
    path = _cache_path()
    temporary_path: str | None = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            delete=False,
        ) as temporary_file:
            json.dump(payload, temporary_file, ensure_ascii=False)
            temporary_file.flush()
            temporary_path = temporary_file.name
        os.replace(temporary_path, path)
    except OSError:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except OSError:
                pass


def save_cached_jobs(jobs: list[Job]) -> None:
    payload = _read_cache()
    payload["jobs"] = [job.model_dump(mode="json") for job in jobs]
    _write_cache(payload)


def load_cached_jobs() -> list[Job] | None:
    payload = _read_cache()
    raw_jobs = payload.get("jobs")
    if not isinstance(raw_jobs, list):
        return None

    jobs = []
    for raw_job in raw_jobs:
        if isinstance(raw_job, dict):
            try:
                jobs.append(Job.model_validate(raw_job))
            except (TypeError, ValueError):
                continue
    return jobs


def save_cached_locations(query: str, locations: tuple[LocationResult, ...]) -> None:
    payload = _read_cache()
    cached_locations = payload.setdefault("locations", {})
    if not isinstance(cached_locations, dict):
        cached_locations = {}
        payload["locations"] = cached_locations
    cached_locations[query.strip().lower()] = [list(location) for location in locations]
    _write_cache(payload)


def load_cached_locations(query: str) -> tuple[LocationResult, ...]:
    payload = _read_cache()
    cached_locations = payload.get("locations")
    if not isinstance(cached_locations, dict):
        return ()

    raw_locations = cached_locations.get(query.strip().lower())
    if not isinstance(raw_locations, list):
        return ()

    locations = []
    for raw_location in raw_locations:
        if not isinstance(raw_location, list) or len(raw_location) != 5:
            continue
        name, latitude, longitude, admin1, country = raw_location
        if (
            isinstance(name, str)
            and isinstance(latitude, (int, float))
            and isinstance(longitude, (int, float))
            and isinstance(admin1, str)
            and isinstance(country, str)
        ):
            locations.append(
                (name, float(latitude), float(longitude), admin1, country)
            )
    return tuple(locations)
