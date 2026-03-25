from fastapi import FastAPI
from fastapi.security import OAuth2PasswordBearer
from app.database import engine, Base
from app import models
from app.routers import jobs, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Smart Hiring Analytics Platform",
    description="Backend + Data Engineering + AI project",
    version="1.0.0"
)

app.include_router(jobs.router)
app.include_router(auth.router)

@app.get("/")
def root():
    return {
        "project": "Smart Hiring Analytics Platform",
        "status":  "running",
        "version": "1.0.0"
    }