from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from pydantic import EmailStr

from ..database import SessionLocal
from ..models import Task
from ..schemas import (
    TaskCreate,
    TaskResponse,
    TaskUpdate
)


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
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
# CREATE TASK
# ============================================================

@router.post(
    "/",
    response_model=TaskResponse
)
def create_task(
    task: TaskCreate,
    db: Session = Depends(get_db)
):

    candidate_id = (
        str(task.candidate_id)
        .strip()
        .lower()
    )

    # ========================================================
    # DUPLICATE CHECK
    # ========================================================

    existing_task = (
        db.query(Task)
        .filter(
            Task.candidate_id == candidate_id,
            Task.source_email_id == task.source_email_id
        )
        .first()
    )

    if existing_task:

        raise HTTPException(
            status_code=409,
            detail=(
                "A task already exists for this "
                "candidate and email."
            )
        )

    # ========================================================
    # CREATE
    # ========================================================

    new_task = Task(

        candidate_id=candidate_id,

        source_email_id=task.source_email_id,

        thread_id=task.thread_id,

        title=task.title,

        description=task.description,

        assignee_id=task.assignee_id.value,

        category=task.category.value,

        priority=task.priority.value,

        due_date=task.due_date,

        deal_value_inr=task.deal_value_inr,

        company_name=task.company_name,

        confidence=task.confidence
    )

    db.add(new_task)

    try:

        db.commit()

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "A task already exists for this "
                "candidate and email."
            )
        )

    db.refresh(new_task)

    return new_task


# ============================================================
# GET TASKS
# ============================================================

@router.get(
    "/",
    response_model=list[TaskResponse]
)
def get_tasks(

    # IMPORTANT:
    # candidate_id is now OPTIONAL.
    # This fixes the frontend 422 error when React calls
    # GET /tasks/ without a candidate_id.

    candidate_id: EmailStr | None = None,

    thread_id: str | None = None,

    source_email_id: str | None = None,

    assignee_id: str | None = None,

    db: Session = Depends(get_db)

):

    query = db.query(Task)

    # ========================================================
    # OPTIONAL CANDIDATE FILTER
    # ========================================================

    if candidate_id:

        candidate_id = (
            str(candidate_id)
            .strip()
            .lower()
        )

        query = query.filter(
            Task.candidate_id == candidate_id
        )

    # ========================================================
    # OPTIONAL THREAD FILTER
    # ========================================================

    if thread_id:

        query = query.filter(
            Task.thread_id == thread_id
        )

    # ========================================================
    # OPTIONAL EMAIL FILTER
    # ========================================================

    if source_email_id:

        query = query.filter(
            Task.source_email_id == source_email_id
        )

    # ========================================================
    # OPTIONAL ASSIGNEE FILTER
    # ========================================================

    if assignee_id:

        query = query.filter(
            Task.assignee_id == assignee_id
        )

    # Newest tasks first
    return (
        query
        .order_by(Task.id.desc())
        .all()
    )


# ============================================================
# GET SINGLE TASK
# ============================================================

@router.get(
    "/{task_id}",
    response_model=TaskResponse
)
def get_task(

    task_id: int,

    db: Session = Depends(get_db)

):

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id
        )
        .first()
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


# ============================================================
# UPDATE TASK
# ============================================================

@router.patch(
    "/{task_id}",
    response_model=TaskResponse
)
def update_task(

    task_id: int,

    task_update: TaskUpdate,

    db: Session = Depends(get_db)

):

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id
        )
        .first()
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    update_data = task_update.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():

        if hasattr(value, "value"):

            value = value.value

        setattr(
            task,
            field,
            value
        )

    db.commit()

    db.refresh(task)

    return task


# ============================================================
# DELETE TASK
# ============================================================

@router.delete(
    "/{task_id}"
)
def delete_task(

    task_id: int,

    db: Session = Depends(get_db)

):

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id
        )
        .first()
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    db.delete(task)

    db.commit()

    return {
        "message": "Task deleted successfully"
    }