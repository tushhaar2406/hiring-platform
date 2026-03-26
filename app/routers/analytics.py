from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.database import get_db
from app.models import Job, User
from app.dependencies import get_current_user
from app.cache import get_cache, set_cache
from collections import Counter

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

# ─── Overview — total jobs, companies, locations ────────────
@router.get("/overview")
def get_overview(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    cache_key = "analytics:overview"
    cached    = get_cache(cache_key)
    if cached:
        return cached

    total_jobs      = db.query(func.count(Job.id)).scalar()
    total_companies = db.query(func.count(func.distinct(Job.company))).scalar()
    total_locations = db.query(func.count(func.distinct(Job.location))).scalar()

    result = {
        "total_jobs":      total_jobs,
        "total_companies": total_companies,
        "total_locations": total_locations,
    }

    set_cache(cache_key, result, expire_seconds=600)
    return result

# ─── Top companies by job count ─────────────────────────────
@router.get("/top-companies")
def get_top_companies(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
    limit:        int     = 10
):
    cache_key = f"analytics:top_companies:{limit}"
    cached    = get_cache(cache_key)
    if cached:
        return cached

    results = (
        db.query(Job.company, func.count(Job.id).label("job_count"))
        .group_by(Job.company)
        .order_by(desc("job_count"))
        .limit(limit)
        .all()
    )

    data = [{"company": r.company, "job_count": r.job_count} for r in results]
    set_cache(cache_key, data, expire_seconds=600)
    return data

# ─── Jobs by location ──────────────────────────────────────
@router.get("/jobs-by-location")
def get_jobs_by_location(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
    limit:        int     = 10
):
    cache_key = f"analytics:jobs_by_location:{limit}"
    cached    = get_cache(cache_key)
    if cached:
        return cached

    results = (
        db.query(Job.location, func.count(Job.id).label("job_count"))
        .group_by(Job.location)
        .order_by(desc("job_count"))
        .limit(limit)
        .all()
    )

    data = [{"location": r.location, "job_count": r.job_count} for r in results]
    set_cache(cache_key, data, expire_seconds=600)
    return data

# ─── Top skills in demand ──────────────────────────────────
@router.get("/top-skills")
def get_top_skills(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
    limit:        int     = 15
):
    cache_key = f"analytics:top_skills:{limit}"
    cached    = get_cache(cache_key)
    if cached:
        return cached

    # common tech skills to look for in title and description
    tech_skills = [
        "python", "java", "javascript", "react", "node",
        "fastapi", "django", "flask", "sql", "postgresql",
        "mysql", "mongodb", "redis", "docker", "kubernetes",
        "aws", "azure", "gcp", "spark", "airflow",
        "pandas", "machine learning", "deep learning", "nlp",
        "git", "linux", "rest api", "microservices", "devops"
    ]

    skill_counter = Counter()

    # fetch all job titles and descriptions
    jobs = db.query(Job.title, Job.description, Job.skills).all()

    for job in jobs:
        # combine title + description + skills into one searchable string
        text = " ".join(filter(None, [
            job.title       or "",
            job.description or "",
            job.skills      or ""
        ])).lower()

        # count how many jobs mention each skill
        for skill in tech_skills:
            if skill in text:
                skill_counter[skill] += 1

    top_skills = [
        {"skill": skill, "count": count}
        for skill, count in skill_counter.most_common(limit)
        if count > 0   # only show skills that actually appear
    ]

    set_cache(cache_key, top_skills, expire_seconds=600)
    return top_skills
# ─── Salary insights ───────────────────────────────────────
@router.get("/salary-insights")
def get_salary_insights(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    cache_key = "analytics:salary_insights"
    cached    = get_cache(cache_key)
    if cached:
        return cached

    # only look at jobs that have salary data
    result = db.query(
        func.avg(Job.salary_min).label("avg_salary_min"),
        func.avg(Job.salary_max).label("avg_salary_max"),
        func.max(Job.salary_max).label("highest_salary"),
        func.min(Job.salary_min).label("lowest_salary"),
        func.count(Job.id).label("jobs_with_salary")
    ).filter(
        Job.salary_min.isnot(None),
        Job.salary_max.isnot(None)
    ).first()

    data = {
        "avg_salary_min":    round(result.avg_salary_min or 0, 2),
        "avg_salary_max":    round(result.avg_salary_max or 0, 2),
        "highest_salary":    result.highest_salary or 0,
        "lowest_salary":     result.lowest_salary  or 0,
        "jobs_with_salary":  result.jobs_with_salary
    }

    set_cache(cache_key, data, expire_seconds=600)
    return data

# ─── Search jobs by keyword ────────────────────────────────
@router.get("/search")
def search_jobs(
    keyword:      str,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    # search across ALL useful columns including location
    results = db.query(Job).filter(
        Job.title.ilike(f"%{keyword}%")       |
        Job.company.ilike(f"%{keyword}%")     |
        Job.location.ilike(f"%{keyword}%")    |
        Job.description.ilike(f"%{keyword}%") |
        Job.skills.ilike(f"%{keyword}%")
    ).limit(20).all()

    if not results:
        return {
            "keyword":  keyword,
            "found":    0,
            "results":  [],
            "message":  f"No jobs found for '{keyword}'"
        }

    return {
        "keyword": keyword,
        "found":   len(results),
        "results": [
            {
                "id":       job.id,
                "title":    job.title,
                "company":  job.company,
                "location": job.location,
                "skills":   job.skills
            }
            for job in results
        ]
    }