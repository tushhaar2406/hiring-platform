from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import PipelineLog, User
from app.schemas import PipelineLogResponse
from app.dependencies import get_current_user
from app.pipeline.etl import run_pipeline
from fastapi.background import BackgroundTasks

router = APIRouter(
    prefix="/pipeline",
    tags=["Pipeline"]
)

# ─── Trigger pipeline manually ─────────────────────────────
@router.post("/run")
def trigger_pipeline(
    background_tasks: BackgroundTasks,
    current_user:     User    = Depends(get_current_user),
    keyword:          str     = "Python",
    location:         str     = "india"
):
    # runs in background — API responds immediately
    # user does not have to wait for pipeline to finish
    background_tasks.add_task(run_pipeline, keyword=keyword, location=location)
    return {
        "message": "Pipeline started in background",
        "keyword": keyword,
        "location": location
    }

# ─── Get all pipeline run logs ─────────────────────────────
@router.get("/logs", response_model=List[PipelineLogResponse])
def get_pipeline_logs(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    logs = db.query(PipelineLog).order_by(PipelineLog.run_date.desc()).all()
    return logs