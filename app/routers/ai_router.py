from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, Resume, User
from app.schemas import ResumeSubmit, ResumeMatchResponse, JobMatch
from app.dependencies import get_current_user
from app.ai import extract_skills_from_resume, match_resume_to_all_jobs, generate_career_advice

router = APIRouter(
    prefix="/ai",
    tags=["AI Features"]
)

@router.post("/match-resume", response_model=ResumeMatchResponse)
def match_resume(
    submission:   ResumeSubmit,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    if len(submission.resume_text.strip()) < 50:
        raise HTTPException(
            status_code=400,
            detail="Resume text too short — please paste your full resume"
        )

    print(f"Analysing resume for user: {current_user.username}")

    try:
        # ── Step 1: Extract skills — 1 API call ───────────
        print("Step 1 — Extracting skills...")
        resume_data      = extract_skills_from_resume(submission.resume_text)
        resume_summary   = resume_data.get("summary", "")
        extracted_skills = resume_data.get("skills", [])
        print(f"Skills found: {extracted_skills}")

        # ── Step 2: Save resume to DB ──────────────────────
        new_resume = Resume(
            user_id          = current_user.id,
            resume_text      = submission.resume_text,
            extracted_skills = ", ".join(extracted_skills)
        )
        db.add(new_resume)
        db.commit()

        # ── Step 3: Fetch jobs ─────────────────────────────
        print("Step 2 — Fetching jobs...")
        jobs = db.query(Job).limit(10).all()   # limit to 10 for free tier

        if not jobs:
            raise HTTPException(
                status_code=404,
                detail="No jobs in database — run the pipeline first"
            )

        # ── Step 4: Match ALL jobs — 1 API call ───────────
        print("Step 3 — Matching against jobs in one call...")
        jobs_list = [
            {
                "id":          job.id,
                "title":       job.title,
                "company":     job.company,
                "location":    job.location or "",
                "description": job.description or ""
            }
            for job in jobs
        ]

        match_results = match_resume_to_all_jobs(extracted_skills, jobs_list)

        # map job_id to job details for easy lookup
        job_lookup = {job.id: job for job in jobs}

        # map job_id to match result
        match_lookup = {m.get("job_id"): m for m in match_results}

        # build JobMatch list
        job_matches = []
        for job in jobs:
            match = match_lookup.get(job.id, {})
            job_matches.append(JobMatch(
                job_id          = job.id,
                title           = job.title,
                company         = job.company,
                location        = job.location,
                match_score     = float(match.get("match_score", 0)),
                matching_skills = match.get("matching_skills", []),
                missing_skills  = match.get("missing_skills", [])
            ))

        # sort by match score
        job_matches.sort(key=lambda x: x.match_score, reverse=True)
        top_5_matches = job_matches[:5]

        # ── Step 5: Career advice — 1 API call ────────────
        print("Step 4 — Generating career advice...")
        matches_dict  = [m.dict() for m in top_5_matches]
        career_advice = generate_career_advice(resume_summary, matches_dict)

        print("Done.")

        return ResumeMatchResponse(
            resume_summary   = resume_summary,
            extracted_skills = extracted_skills,
            top_matches      = top_5_matches,
            overall_advice   = career_advice
        )

    except HTTPException:
        raise

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(
            status_code=503,
            detail=f"AI service error: {str(e)}"
        )

# ─── Resume history ────────────────────────────────────────
@router.get("/my-resumes")
def get_my_resumes(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    resumes = db.query(Resume).filter(
        Resume.user_id == current_user.id
    ).order_by(Resume.created_at.desc()).all()

    return [
        {
            "id":               r.id,
            "extracted_skills": r.extracted_skills,
            "created_at":       str(r.created_at)
        }
        for r in resumes
    ]
