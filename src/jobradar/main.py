from pathlib import Path

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jobradar.api.routes.jobs import router as jobs_router
from jobradar.schemas.job import Job
from jobradar.services.sync import preview_jobs

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
def read_root(request: Request, remote_only: bool = Query(default=False)):
    offline = False
    try:
        result = preview_jobs(limit=12, remote_only=remote_only)
        jobs = result.jobs
    except httpx.HTTPError:
        jobs = [job for job in FALLBACK_JOBS if not remote_only or job.remote]
        offline = True

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": "JobRadar",
            "jobs": jobs,
            "remote_only": remote_only,
            "offline": offline,
        },
    )


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
