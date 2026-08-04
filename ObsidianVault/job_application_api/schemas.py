from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from models import ApplicationStatus

class JobApplicationBase(BaseModel):
    company: str = Field(..., description="Company name", json_schema_extra={"example": "Google"})
    position: str = Field(..., description="Job position/title", json_schema_extra={"example": "Senior Software Engineer"})
    status: ApplicationStatus = Field(default=ApplicationStatus.APPLIED, description="Current application status")
    application_date: date = Field(default_factory=date.today, description="Date application was submitted")
    job_url: Optional[str] = Field(None, description="URL of job posting")
    location: Optional[str] = Field(None, description="Job location (e.g. Remote, City)")
    salary_range: Optional[str] = Field(None, description="Expected or listed salary range")
    notes: Optional[str] = Field(None, description="Custom notes regarding interview or follow ups")

class JobApplicationCreate(JobApplicationBase):
    pass

class JobApplicationUpdate(BaseModel):
    company: Optional[str] = None
    position: Optional[str] = None
    status: Optional[ApplicationStatus] = None
    application_date: Optional[date] = None
    job_url: Optional[str] = None
    location: Optional[str] = None
    salary_range: Optional[str] = None
    notes: Optional[str] = None

class JobApplicationResponse(JobApplicationBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
