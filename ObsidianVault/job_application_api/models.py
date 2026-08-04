import enum
from datetime import datetime, date, timezone
# pyrefly: ignore [missing-import]
from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Enum
from database import Base

class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    REJECTED = "rejected"
    FOLLOW_UP = "follow_up"
    SCHEDULED_INTERVIEW = "scheduled_interview"
    ADDITIONAL_INFO_NEEDED = "additional_info_needed"

class JobApplication(Base):
    __tablename__ = "job_applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String(255), nullable=False, index=True)
    position = Column(String(255), nullable=False, index=True)
    status = Column(Enum(ApplicationStatus), nullable=False, default=ApplicationStatus.APPLIED, index=True)
    application_date = Column(Date, nullable=False, default=date.today)
    job_url = Column(String(500), nullable=True)
    location = Column(String(255), nullable=True)
    salary_range = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

