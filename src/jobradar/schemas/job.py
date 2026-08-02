from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl


class Job(BaseModel):
    source: str
    source_id: str
    title: str
    company: str
    location: str | None = None
    remote: bool = False
    url: HttpUrl
    description_html: str
    tags: list[str] = Field(default_factory=list)
    job_types: list[str] = Field(default_factory=list)
    posted_at: datetime | None = None


class JobPreviewResponse(BaseModel):
    source: str
    count: int
    jobs: list[Job]
