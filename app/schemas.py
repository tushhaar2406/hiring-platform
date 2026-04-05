from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from typing import Optional, List

# ─── Job schemas ───────────────────────────────────────────

# what user sends when CREATING a job — all required fields
class JobCreate(BaseModel):
    title:       str
    company:     str
    location:    Optional[str] = None
    salary_min:  Optional[float] = None
    salary_max:  Optional[float] = None
    description: Optional[str] = None
    skills:      Optional[str] = None
    source:      Optional[str] = None

# what user sends when UPDATING a job — all fields optional
# because user might want to update only one field
class JobUpdate(BaseModel):
    title:       Optional[str] = None
    company:     Optional[str] = None
    location:    Optional[str] = None
    salary_min:  Optional[float] = None
    salary_max:  Optional[float] = None
    description: Optional[str] = None
    skills:      Optional[str] = None

# what your API sends BACK to the user — includes id and timestamps
class JobResponse(BaseModel):
    id:          int
    title:       str
    company:     str
    location:    Optional[str] = None
    salary_min:  Optional[float] = None
    salary_max:  Optional[float] = None
    description: Optional[str] = None
    skills:      Optional[str] = None
    source:      Optional[str] = None
    posted_date: Optional[date] = None
    created_at:  Optional[datetime] = None

    class Config:
        from_attributes = True  # allows SQLAlchemy model to convert to this schema



# ─── User schemas ──────────────────────────────────────────

class UserCreate(BaseModel):
    email:    str
    username: str
    password: str         # plain password — we hash it before storing

class UserResponse(BaseModel):
    id:         int
    email:      str
    username:   str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type:   str    # always "bearer"


# ─── Pipeline schemas ──────────────────────────────────────

class PipelineLogResponse(BaseModel):
    id:            int
    run_date:      Optional[datetime] = None
    jobs_fetched:  int
    jobs_inserted: int
    jobs_skipped:  int
    status:        str
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

# ─── Resume schemas ────────────────────────────────────────

class ResumeSubmit(BaseModel):
    resume_text: str              # user pastes their resume here

class JobMatch(BaseModel):
    job_id:         int
    title:          str
    company:        str
    location:       Optional[str] = None
    match_score:    float         # 0 to 100
    matching_skills: List[str]    # skills user has that match
    missing_skills:  List[str]    # skills user lacks

class ResumeMatchResponse(BaseModel):
    resume_summary:   str         # Claude's summary of the resume
    extracted_skills: List[str]   # all skills Claude found in resume
    top_matches:      List[JobMatch]  # top 5 matching jobs
    overall_advice:   str         # Claude's career advice