from sqlalchemy import Column, Integer, String, Text, Date, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base
import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

class Job(Base):
    __tablename__ = "jobs"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(100), nullable=False)
    company     = Column(String(100), nullable=False)
    location    = Column(String(100), nullable=True)
    salary_min  = Column(Float,       nullable=True)
    salary_max  = Column(Float,       nullable=True)
    description = Column(Text,        nullable=True)
    skills      = Column(Text,        nullable=True)
    source      = Column(String(50),  nullable=True)
    posted_date = Column(Date,        default=datetime.date.today)
    created_at  = Column(DateTime,    default=func.now())

class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    email           = Column(String(100), unique=True, nullable=False)
    username        = Column(String(50),  unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at      = Column(DateTime,    default=func.now())

class PipelineLog(Base):
    __tablename__ = "pipeline_logs"

    id            = Column(Integer, primary_key=True, index=True)
    run_date      = Column(DateTime, default=func.now())
    jobs_fetched  = Column(Integer, default=0)   # how many came from API
    jobs_inserted = Column(Integer, default=0)   # how many were new
    jobs_skipped  = Column(Integer, default=0)   # how many already existed
    status        = Column(String(20), default="success")  # success or failed
    error_message = Column(Text, nullable=True)  # if failed — why



class Resume(Base):
    __tablename__ = "resumes"

    id               = Column(Integer, primary_key=True, index=True)
    user_id          = Column(Integer, ForeignKey("users.id"), nullable=False)
    resume_text      = Column(Text, nullable=False)      # raw resume content
    extracted_skills = Column(Text, nullable=True)       # skills Claude finds
    created_at       = Column(DateTime, default=func.now())

    # relationship — links back to User
    user = relationship("User", backref="resumes")