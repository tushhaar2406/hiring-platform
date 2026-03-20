from fastapi import FastAPI
from app.database import engine, Base

# this line is critical — imports models so SQLAlchemy knows about them
from app import models

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Hiring Analytics Platform",
    description="Backend + Data Engineering + AI project",
    version="1.0.0"
)

@app.get("/")
def root():
    return {
        "project": "Smart Hiring Analytics Platform",
        "status":  "running",
        "version": "1.0.0"
    }