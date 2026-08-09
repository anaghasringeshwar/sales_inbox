from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import EmailStr

from ..database import SessionLocal
from ..models import Task, ProcessedEmail


router = APIRouter(
    prefix="/api",
    tags=["API"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/tasks")
def get_api_tasks(
    candidate_id: EmailStr,
    db: Session = Depends(get_db)
):

    candidate_id = candidate_id.strip().lower()

    # Get tasks
    tasks = (
        db.query(Task)
        .filter(Task.candidate_id == candidate_id)
        .all()
    )

    # Get processed emails
    processed = (
        db.query(ProcessedEmail)
        .filter(
            ProcessedEmail.candidate_id == candidate_id
        )
        .all()
    )

    return {
        "tasks": [
            {
                "id": task.id,
                "candidate_id": task.candidate_id,
                "source_email_id": task.source_email_id,
                "thread_id": task.thread_id,
                "title": task.title,
                "description": task.description,
                "assignee_id": task.assignee_id,
                "category": task.category,
                "priority": task.priority,
                "due_date": task.due_date,
                "deal_value_inr": task.deal_value_inr,
                "company_name": task.company_name,
                "confidence": task.confidence
            }
            for task in tasks
        ],

        "processed": len(processed),

        "skipped": [
            {
                "email_id": email.email_id,
                "thread_id": email.thread_id,
                "category": email.category,
                "reason": email.reason,
                "confidence": email.confidence
            }
            for email in processed
            if email.decision == "skipped"
        ]
    }