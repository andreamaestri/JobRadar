from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from jobradar.api.routes.jobs import router as jobs_router

app = FastAPI()

BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

app.include_router(jobs_router)


@app.get("/", include_in_schema=False)
def read_root(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"app_name": "JobRadar"},
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
