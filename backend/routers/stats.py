from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import EmailStr

from ..database import SessionLocal
from ..models import Task, ProcessedEmail


router = APIRouter(
    prefix="/api",
    tags=["Stats"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/stats")
def get_stats(
    candidate_id: EmailStr,
    db: Session = Depends(get_db)
):

    candidate_id = candidate_id.strip().lower()

    # Get all tasks
    tasks = (
        db.query(Task)
        .filter(Task.candidate_id == candidate_id)
        .all()
    )

    # Get all processed emails
    processed = (
        db.query(ProcessedEmail)
        .filter(
            ProcessedEmail.candidate_id == candidate_id
        )
        .all()
    )

    return {
        "candidate_id": candidate_id,

        "total_emails_processed": len(processed),

        "tasks_created": sum(
            1
            for email in processed
            if email.decision == "created"
        ),

        "tasks_updated": sum(
            1
            for email in processed
            if email.decision == "updated"
        ),

        "emails_skipped": sum(
            1
            for email in processed
            if email.decision == "skipped"
        ),

        "total_tasks": len(tasks),

        "high_priority_tasks": sum(
            1
            for task in tasks
            if task.priority == "high"
        ),

        "medium_priority_tasks": sum(
            1
            for task in tasks
            if task.priority == "medium"
        ),

        "low_priority_tasks": sum(
            1
            for task in tasks
            if task.priority == "low"
        )
    }