from sqlalchemy import Column, Integer, String, Text, Date, Float, DateTime
from sqlalchemy.sql import func
from app.database import Base
import datetime

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