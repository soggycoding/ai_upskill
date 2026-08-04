from typing import List, Optional
# pyrefly: ignore [missing-import]
from fastapi import FastAPI, Depends, HTTPException, Query, status
# pyrefly: ignore [missing-import]
from sqlalchemy.orm import Session

import models
import schemas
import crud
from database import engine, get_db
from models import ApplicationStatus

# Automatically create tables in SQLite database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Job Application Tracker API",
    description=(
        "A RESTful API to manage job applications and filter them by status:\n"
        "- `rejected`\n"
        "- `follow_up`\n"
        "- `scheduled_interview`\n"
        "- `additional_info_needed`\n"
        "- `applied`"
    ),
    version="1.0.0"
)

@app.get("/", tags=["Health"])
def root():
    """Health check & root endpoint providing API metadata."""
    return {
        "status": "online",
        "message": "Welcome to the RESTful Job Application Tracker API",
        "docs_url": "/docs",
        "available_statuses": [s.value for s in ApplicationStatus]
    }

@app.post(
    "/api/applications/", 
    response_model=schemas.JobApplicationResponse, 
    status_code=status.HTTP_201_CREATED, 
    tags=["Applications"]
)
def create_application(
    application: schemas.JobApplicationCreate, 
    db: Session = Depends(get_db)
):
    """Create a new job application entry."""
    return crud.create_job_application(db=db, application=application)

@app.get(
    "/api/applications/", 
    response_model=List[schemas.JobApplicationResponse], 
    tags=["Applications"]
)
def list_applications(
    status: Optional[ApplicationStatus] = Query(
        None, 
        description="Filter applications by status (e.g., rejected, follow_up, scheduled_interview, additional_info_needed)"
    ),
    search: Optional[str] = Query(None, description="Search by company or position name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """List job applications with optional status filter and text search."""
    return crud.get_job_applications(db=db, status=status, search=search, skip=skip, limit=limit)

@app.get(
    "/api/applications/{application_id}", 
    response_model=schemas.JobApplicationResponse, 
    tags=["Applications"]
)
def get_application(application_id: int, db: Session = Depends(get_db)):
    """Get details of a single job application by ID."""
    db_application = crud.get_job_application(db=db, application_id=application_id)
    if db_application is None:
        raise HTTPException(status_code=404, detail="Job application not found")
    return db_application

@app.patch(
    "/api/applications/{application_id}", 
    response_model=schemas.JobApplicationResponse, 
    tags=["Applications"]
)
def update_application(
    application_id: int, 
    application_update: schemas.JobApplicationUpdate, 
    db: Session = Depends(get_db)
):
    """Update status, notes, or details of an existing job application."""
    updated_app = crud.update_job_application(db=db, application_id=application_id, application_update=application_update)
    if updated_app is None:
        raise HTTPException(status_code=404, detail="Job application not found")
    return updated_app

@app.delete(
    "/api/applications/{application_id}", 
    status_code=status.HTTP_204_NO_CONTENT, 
    tags=["Applications"]
)
def delete_application(application_id: int, db: Session = Depends(get_db)):
    """Delete a job application entry."""
    success = crud.delete_job_application(db=db, application_id=application_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job application not found")
    return None

# Convenience Category Filter Endpoints

@app.get(
    "/api/applications/filter/rejected", 
    response_model=List[schemas.JobApplicationResponse], 
    tags=["Category Filters"]
)
def get_rejected_applications(db: Session = Depends(get_db)):
    """Filter out and return all REJECTED applications."""
    return crud.get_job_applications(db=db, status=ApplicationStatus.REJECTED)

@app.get(
    "/api/applications/filter/follow-up", 
    response_model=List[schemas.JobApplicationResponse], 
    tags=["Category Filters"]
)
def get_follow_up_applications(db: Session = Depends(get_db)):
    """Filter out and return all applications marked for FOLLOW UP."""
    return crud.get_job_applications(db=db, status=ApplicationStatus.FOLLOW_UP)

@app.get(
    "/api/applications/filter/scheduled-interview", 
    response_model=List[schemas.JobApplicationResponse], 
    tags=["Category Filters"]
)
def get_scheduled_interview_applications(db: Session = Depends(get_db)):
    """Filter out and return all applications with a SCHEDULED INTERVIEW."""
    return crud.get_job_applications(db=db, status=ApplicationStatus.SCHEDULED_INTERVIEW)

@app.get(
    "/api/applications/filter/additional-info-needed", 
    response_model=List[schemas.JobApplicationResponse], 
    tags=["Category Filters"]
)
def get_additional_info_needed_applications(db: Session = Depends(get_db)):
    """Filter out and return all applications requiring ADDITIONAL INFORMATION."""
    return crud.get_job_applications(db=db, status=ApplicationStatus.ADDITIONAL_INFO_NEEDED)
