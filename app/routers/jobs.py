from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import Job
from app.schemas import JobCreate, JobUpdate, JobResponse
from app.dependencies import get_current_user
from app.models import User
from app.cache import get_cache, set_cache, delete_cache 
router = APIRouter(
    prefix="/jobs",       # all routes here start with /jobs
    tags=["Jobs"]         # groups them together in Swagger UI
)

# ─── CREATE a job ─────────────────────────────────────────
# ─── CREATE a job ──────────────────────────────────────────
@router.post("/", response_model=JobResponse, status_code=201)
def create_job(
    job:          JobCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    new_job = Job(**job.model_dump())
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    delete_cache("jobs:all")   # ← clear cache so next GET fetches fresh data
    return new_job

# ─── GET all jobs — with Redis caching ─────────────────────
@router.get("/", response_model=List[JobResponse])
def get_all_jobs(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    cache_key = "jobs:all"

    # step 1 — check cache first
    cached = get_cache(cache_key)
    if cached:
        print("Cache HIT — returning from Redis")
        return cached

    # step 2 — cache miss — fetch from PostgreSQL
    print("Cache MISS — fetching from PostgreSQL")
    jobs = db.query(Job).all()

    # step 3 — convert to dict for JSON serialization
    jobs_data = [
        {
            "id":          job.id,
            "title":       job.title,
            "company":     job.company,
            "location":    job.location,
            "salary_min":  job.salary_min,
            "salary_max":  job.salary_max,
            "description": job.description,
            "skills":      job.skills,
            "source":      job.source,
            "posted_date": str(job.posted_date) if job.posted_date else None,
            "created_at":  str(job.created_at)  if job.created_at  else None,
        }
        for job in jobs
    ]

    # step 4 — store in cache for 5 minutes
    set_cache(cache_key, jobs_data, expire_seconds=300)

    return jobs_data

# ─── GET one job by id ─────────────────────────────────────
@router.get("/{job_id}", response_model=JobResponse)
def get_one_job(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    job = db.query(Job).filter(Job.id == job_id).first()  # SELECT * FROM jobs WHERE id = job_id
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    return job

# ─── UPDATE a job ──────────────────────────────────────────
@router.put("/{job_id}", response_model=JobResponse)
def update_job(job_id: int, updated: JobUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
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
    delete_cache("jobs:all")   # ← clear cache so next GET fetches fresh data
    return job

# ─── DELETE a job ──────────────────────────────────────────
@router.delete("/{job_id}", status_code=204)
def delete_job(
    job_id:       int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with id {job_id} not found"
        )
    db.delete(job)
    db.commit()
    delete_cache("jobs:all")   # ← clear cache so next GET fetches fresh data
    return