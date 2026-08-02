from fastapi import FastAPI

from jobradar.api.routes.jobs import router as jobs_router

app = FastAPI()

app.include_router(jobs_router)


@app.get("/")
def read_root():
    return {
        "app": "JobRadar",
        "message": "Welcome to JobRadar!",
        "endpoints": {
            "about": "/about",
            "jobs_preview": "/api/jobs/preview",
        },
    }


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
