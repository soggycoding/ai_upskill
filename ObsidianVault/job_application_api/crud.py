from typing import List, Optional
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

from models import JobApplication, ApplicationStatus
from schemas import JobApplicationCreate, JobApplicationUpdate

def create_job_application(db: Session, application: JobApplicationCreate) -> JobApplication:
    """Create a new job application record in database."""
    db_obj = JobApplication(**application.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_job_application(db: Session, application_id: int) -> Optional[JobApplication]:
    """Retrieve a single job application by ID."""
    return db.query(JobApplication).filter(JobApplication.id == application_id).first()

def get_job_applications(
    db: Session, 
    status: Optional[ApplicationStatus] = None, 
    search: Optional[str] = None,
    skip: int = 0, 
    limit: int = 100
) -> List[JobApplication]:
    """Retrieve multiple job applications with optional status filter and search query."""
    query = db.query(JobApplication)
    if status:
        query = query.filter(JobApplication.status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (JobApplication.company.ilike(search_pattern)) | 
            (JobApplication.position.ilike(search_pattern))
        )
    return query.order_by(JobApplication.updated_at.desc()).offset(skip).limit(limit).all()

def update_job_application(
    db: Session, 
    application_id: int, 
    application_update: JobApplicationUpdate
) -> Optional[JobApplication]:
    """Update fields or status of an existing job application."""
    db_obj = get_job_application(db, application_id)
    if not db_obj:
        return None
    
    update_data = application_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_job_application(db: Session, application_id: int) -> bool:
    """Delete a job application by ID."""
    db_obj = get_job_application(db, application_id)
    if not db_obj:
        return False
    db.delete(db_obj)
    db.commit()
    return True
