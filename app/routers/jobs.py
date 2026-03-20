from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Job
from app.schemas import JobCreate, JobUpdate, JobResponse

router = APIRouter(
    prefix="/jobs",       # all routes here start with /jobs
    tags=["Jobs"]         # groups them together in Swagger UI
)

# ─── CREATE a job ─────────────────────────────────────────
@router.post("/", response_model=JobResponse, status_code=201)
def create_job(job: JobCreate, db: Session = Depends(get_db)):
    # job is already validated by Pydantic — safe to use directly
    new_job = Job(**job.model_dump())  # convert schema to SQLAlchemy model
    db.add(new_job)                    # stage the new job
    db.commit()                        # save to PostgreSQL
    db.refresh(new_job)                # get the saved data back — includes id
    return new_job

# ─── GET all jobs ──────────────────────────────────────────
@router.get("/", response_model=List[JobResponse])
def get_all_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()         # SELECT * FROM jobs
    return jobs

# ─── GET one job by id ─────────────────────────────────────
@router.get("/{job_id}", response_model=JobResponse)
def get_one_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()  # SELECT * FROM jobs WHERE id = job_id
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    return job

# ─── UPDATE a job ──────────────────────────────────────────
@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, updated: JobUpdate, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    # only update fields that user actually sent — skip None values
    update_data = updated.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)
    return job

# ─── DELETE a job ──────────────────────────────────────────
@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    db.delete(job)
    db.commit()
    return  # 204 means success with no content returned