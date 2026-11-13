from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class UTCResponse(BaseModel):
    @field_validator("created_at", "finished_at", check_fields=False)
    @classmethod
    def utc_dates(cls, value):
        # SQLite drops timezone information from DateTime(timezone=True).
        return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value


class JobResponse(UTCResponse):
    model_config = ConfigDict(from_attributes=True)
    id: str
    case_id: str
    status: Literal["queued", "running", "completed", "failed"]
    progress: int
    stage: str
    created_at: datetime
    finished_at: datetime | None
    error: str | None
    result: dict | None


class CaseResponse(UTCResponse):
    id: str
    name: str
    created_at: datetime
    geometry: dict
    latest_job: JobResponse | None
