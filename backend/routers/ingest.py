from fastapi import APIRouter, Depends

from sqlalchemy.orm import Session

from datetime import datetime

from ..database import SessionLocal
from ..models import Task, ProcessedEmail
from ..schemas import IngestRequest
from ..classifier import classify_email


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/ingest",
    tags=["Ingest"]
)


# ============================================================
# DATABASE DEPENDENCY
# ============================================================

def get_db():

    db = SessionLocal()

    try:

        yield db

    finally:

        db.close()


# ============================================================
# INGEST
# ============================================================

@router.post("/")
def ingest(

    request: IngestRequest,

    db: Session = Depends(get_db)
):

    # ========================================================
    # NORMALIZE CANDIDATE ID
    # ========================================================

    candidate_id = (
        str(request.candidate_id)
        .strip()
        .lower()
    )

    # ========================================================
    # COUNTERS
    # ========================================================

    processed = 0
    tasks_created = 0
    tasks_updated = 0
    skipped = 0
    duplicates = 0

    errors = []

    # ========================================================
    # PROCESS EACH EMAIL
    # ========================================================

    for email in request.emails:

        decision = None

        try:

            # =================================================
            # IDEMPOTENCY CHECK
            # =================================================

            already_processed = (
                db.query(ProcessedEmail)
                .filter(
                    ProcessedEmail.candidate_id
                    == candidate_id,

                    ProcessedEmail.email_id
                    == email.email_id
                )
                .first()
            )

            if already_processed:

                duplicates += 1

                continue

            # =================================================
            # NEW EMAIL
            # =================================================

            processed += 1

            # =================================================
            # CLASSIFY
            # =================================================

            result = classify_email(email)

            # =================================================
            # SKIPPED EMAIL
            # =================================================

            if result.get("decision") == "skip":

                record = ProcessedEmail(

                    candidate_id=candidate_id,

                    email_id=email.email_id,

                    thread_id=email.thread_id,

                    decision="skipped",

                    category=result.get(
                        "category"
                    ),

                    assignee_id=result.get(
                        "assignee_id"
                    ),

                    confidence=result.get(
                        "confidence"
                    ),

                    reason=result.get(
                        "reason"
                    ),

                    created_at=datetime.now().isoformat()
                )

                db.add(record)

                db.commit()

                skipped += 1

                continue

            # =================================================
            # FIND EXISTING THREAD TASK
            # =================================================

            existing_task = (
                db.query(Task)
                .filter(
                    Task.candidate_id
                    == candidate_id,

                    Task.thread_id
                    == email.thread_id
                )
                .first()
            )

            # =================================================
            # UPDATE EXISTING TASK
            # =================================================

            if existing_task:

                # Always keep the latest email as
                # the source of the task description/title.

                existing_task.title = result.get(
                    "title",
                    existing_task.title
                )

                existing_task.description = result.get(
                    "description",
                    existing_task.description
                )

                # Only update these if Gemini actually
                # returned a value.

                if result.get("assignee_id") is not None:

                    existing_task.assignee_id = (
                        result["assignee_id"]
                    )

                if result.get("category") is not None:

                    existing_task.category = (
                        result["category"]
                    )

                if result.get("priority") is not None:

                    existing_task.priority = (
                        result["priority"]
                    )

                if result.get("due_date") is not None:

                    existing_task.due_date = (
                        result["due_date"]
                    )

                if result.get("deal_value_inr") is not None:

                    existing_task.deal_value_inr = (
                        result["deal_value_inr"]
                    )

                if result.get("company_name") is not None:

                    existing_task.company_name = (
                        result["company_name"]
                    )

                if result.get("confidence") is not None:

                    existing_task.confidence = (
                        result["confidence"]
                    )

                tasks_updated += 1

                decision = "updated"

            # =================================================
            # CREATE NEW TASK
            # =================================================

            else:

                new_task = Task(

                    candidate_id=candidate_id,

                    source_email_id=email.email_id,

                    thread_id=email.thread_id,

                    title=result.get(
                        "title",
                        email.subject
                    ),

                    description=result.get(
                        "description",
                        email.body
                    ),

                    assignee_id=result.get(
                        "assignee_id",
                        "u_triage"
                    ),

                    category=result.get(
                        "category",
                        "triage"
                    ),

                    priority=result.get(
                        "priority",
                        "medium"
                    ),

                    due_date=result.get(
                        "due_date"
                    ),

                    deal_value_inr=result.get(
                        "deal_value_inr"
                    ),

                    company_name=result.get(
                        "company_name"
                    ),

                    confidence=result.get(
                        "confidence",
                        0.5
                    )
                )

                db.add(new_task)

                tasks_created += 1

                decision = "created"

            # =================================================
            # SAVE PROCESSING RECORD
            # =================================================

            record = ProcessedEmail(

                candidate_id=candidate_id,

                email_id=email.email_id,

                thread_id=email.thread_id,

                decision=decision,

                category=result.get(
                    "category"
                ),

                assignee_id=result.get(
                    "assignee_id"
                ),

                confidence=result.get(
                    "confidence"
                ),

                reason=result.get(
                    "reason"
                ),

                created_at=datetime.now().isoformat()
            )

            db.add(record)

            # =================================================
            # COMMIT THIS EMAIL
            # =================================================

            db.commit()

        # =====================================================
        # ERROR HANDLING
        # =====================================================

        except Exception as e:

            db.rollback()

            # Correct counters if the DB operation failed.

            if decision == "created":

                tasks_created -= 1

            elif decision == "updated":

                tasks_updated -= 1

            errors.append({

                "email_id": email.email_id,

                "error": str(e)

            })

    # ========================================================
    # FINAL RESPONSE
    # ========================================================

    return {

        "processed": processed,

        "tasks_created": tasks_created,

        "tasks_updated": tasks_updated,

        "skipped": skipped,

        "duplicates": duplicates,

        "errors": errors
    }