from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..database import SessionLocal
from ..models import Task
from ..classifier import client, MODEL_NAME


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/chat",
    tags=["Chat"]
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
# REQUEST / RESPONSE SCHEMAS
# ============================================================

class ChatMessage(BaseModel):
    role: str      # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ChatResponse(BaseModel):
    reply: str


# ============================================================
# BUILD CONTEXT FROM THE DATABASE
# ============================================================

def build_task_context(db: Session) -> str:
    """
    Turns the most recent tasks into a short text summary
    that we hand to Gemini, so it can answer questions like
    'what are my high priority tasks?' using real data.
    """

    tasks = (
        db.query(Task)
        .order_by(Task.id.desc())
        .limit(50)
        .all()
    )

    if not tasks:
        return "There are currently no tasks in the system."

    lines = []

    for task in tasks:
        lines.append(
            f"- #{task.id} | {task.title} | "
            f"priority={task.priority} | category={task.category} | "
            f"assignee={task.assignee_id} | "
            f"company={task.company_name or 'n/a'} | "
            f"deal_value_inr={task.deal_value_inr or 'n/a'} | "
            f"due_date={task.due_date or 'n/a'}"
        )

    return "\n".join(lines)


# ============================================================
# CHAT ENDPOINT
# ============================================================

@router.post(
    "/",
    response_model=ChatResponse
)
def chat(
    request: ChatRequest,
    db: Session = Depends(get_db)
):

    if not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message cannot be empty."
        )

    task_context = build_task_context(db)

    system_instructions = (
        "You are the assistant inside the SalesInbox app. "
        "You help a sales operations user understand the tasks "
        "that were generated from inbound emails. "
        "Answer questions using the task data provided below. "
        "Be concise and use plain language. If the answer isn't "
        "in the data, say so honestly instead of guessing.\n\n"
        f"Current tasks:\n{task_context}"
    )

    contents = [system_instructions]

    for turn in request.history:
        prefix = "User" if turn.role == "user" else "Assistant"
        contents.append(f"{prefix}: {turn.content}")

    contents.append(f"User: {request.message}")

    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents="\n\n".join(contents)
        )

        reply_text = (response.text or "").strip()

        if not reply_text:
            reply_text = (
                "I couldn't come up with a response. "
                "Try rephrasing your question."
            )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=f"Chat request failed: {error}"
        )

    return ChatResponse(reply=reply_text)