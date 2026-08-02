from datetime import UTC, date, datetime, time
from typing import Any

import httpx
from pydantic import HttpUrl

from jobradar.schemas.job import Job

ARBEITSAGENTUR_SOURCE = "arbeitsagentur"
ARBEITSAGENTUR_API_URL = (
    "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/pc/v6/jobs"
)
ARBEITSAGENTUR_JOB_URL = "https://www.arbeitsagentur.de/jobsuche/suche"
ARBEITSAGENTUR_HEADERS = {"X-API-Key": "jobboerse-jobsuche"}


def fetch_arbeitsagentur_jobs(
    *,
    limit: int,
    remote_only: bool = False,
    query: str | None = None,
    location: str | None = None,
    radius_km: int | None = None,
) -> list[Job]:
    """Fetch job listings from the Bundesagentur für Arbeit Jobsuche service."""
    if limit <= 0:
        return []

    params: dict[str, str | int | bool] = {
        "angebotsart": 1,
        "page": 1,
        "size": min(limit, 100),
        "pav": False,
    }
    if query:
        params["was"] = query
    if location:
        params["wo"] = location
    if location and radius_km is not None:
        params["umkreis"] = radius_km
    if remote_only:
        params["arbeitszeit"] = "ho"

    response = httpx.get(
        ARBEITSAGENTUR_API_URL,
        headers=ARBEITSAGENTUR_HEADERS,
        params=params,
        timeout=15.0,
    )
    response.raise_for_status()

    payload = response.json()
    if not isinstance(payload, dict):
        return []
    raw_jobs = payload.get("ergebnisliste", payload.get("stellenangebote", []))
    if not isinstance(raw_jobs, list):
        return []

    jobs = []
    for raw_job in raw_jobs:
        if not isinstance(raw_job, dict):
            continue
        try:
            job = _normalize_arbeitsagentur_job(raw_job)
        except (KeyError, TypeError, ValueError):
            continue
        if remote_only:
            job = job.model_copy(update={"remote": True})
        jobs.append(job)
        if len(jobs) == limit:
            break
    return jobs


def _normalize_arbeitsagentur_job(raw_job: dict[str, Any]) -> Job:
    reference = raw_job.get("referenznummer") or raw_job["refnr"]
    title = raw_job.get("stellenangebotsTitel") or raw_job.get("beruf")
    company = raw_job.get("firma") or raw_job.get("arbeitgeber")
    if not isinstance(title, str) or not isinstance(company, str):
        raise TypeError("Job is missing a title or company")

    return Job(
        source=ARBEITSAGENTUR_SOURCE,
        source_id=str(reference),
        title=title,
        company=company,
        location=_job_location(raw_job),
        remote=bool(
            raw_job.get("arbeitszeitHomeoffice") or raw_job.get("homeoffice")
        ),
        url=_job_url(raw_job, reference=str(reference)),
        description_html="",
        tags=_coerce_string_list(raw_job.get("alleBerufe"))
        or _coerce_string_list(raw_job.get("beruf")),
        job_types=_job_types(raw_job),
        posted_at=_posted_at(raw_job),
    )


def _job_location(raw_job: dict[str, Any]) -> str | None:
    locations = raw_job.get("stellenlokationen")
    if isinstance(locations, list) and locations and isinstance(locations[0], dict):
        address = locations[0].get("adresse")
        if isinstance(address, dict):
            return _format_location(address)

    address = raw_job.get("arbeitsort")
    if isinstance(address, dict):
        return _format_location(address)
    return None


def _format_location(address: dict[str, Any]) -> str | None:
    parts = [address.get("plz"), address.get("ort"), address.get("region")]
    unique_parts = []
    for part in parts:
        if isinstance(part, (str, int)) and str(part) and str(part) not in unique_parts:
            unique_parts.append(str(part))
    return " ".join(unique_parts) or None


def _job_url(raw_job: dict[str, Any], *, reference: str) -> HttpUrl:
    external_url = raw_job.get("externeUrl")
    if isinstance(external_url, str) and external_url.startswith(("https://", "http://")):
        return HttpUrl(external_url)
    return HttpUrl(f"{ARBEITSAGENTUR_JOB_URL}?id={reference}")


def _job_types(raw_job: dict[str, Any]) -> list[str]:
    job_types = []
    if raw_job.get("arbeitszeitVollzeit"):
        job_types.append("Vollzeit")
    if raw_job.get("arbeitszeitTeilzeit"):
        job_types.append("Teilzeit")
    if raw_job.get("arbeitszeitHomeoffice") or raw_job.get("homeoffice"):
        job_types.append("Homeoffice")
    return job_types


def _posted_at(raw_job: dict[str, Any]) -> datetime | None:
    value = raw_job.get("datumErsteVeroeffentlichung")
    if not isinstance(value, str):
        period = raw_job.get("veroeffentlichungszeitraum")
        if isinstance(period, dict):
            value = period.get("von")
    if not isinstance(value, str):
        return None
    try:
        return datetime.combine(date.fromisoformat(value[:10]), time.min, tzinfo=UTC)
    except ValueError:
        return None


def _coerce_string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    if isinstance(value, str):
        return [value]
    return []
