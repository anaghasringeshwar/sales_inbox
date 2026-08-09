from typing import Optional
from enum import Enum

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    EmailStr,
    field_validator
)


# ============================================================
# ASSIGNEES
# ============================================================

class Assignee(str, Enum):

    u_aarti = "u_aarti"
    u_rohit = "u_rohit"
    u_meera = "u_meera"
    u_karan = "u_karan"
    u_divya = "u_divya"
    u_triage = "u_triage"


# ============================================================
# CATEGORIES
# ============================================================

class Category(str, Enum):

    enterprise_rfp = "enterprise_rfp"
    smb_enquiry = "smb_enquiry"
    marketing = "marketing"
    alliances = "alliances"
    finance = "finance"
    triage = "triage"


# ============================================================
# PRIORITY
# ============================================================

class Priority(str, Enum):

    low = "low"
    medium = "medium"
    high = "high"


# ============================================================
# TASK CREATE
# ============================================================

class TaskCreate(BaseModel):

    candidate_id: EmailStr

    source_email_id: str
    thread_id: str

    title: str
    description: Optional[str] = None

    assignee_id: Assignee
    category: Category
    priority: Priority

    due_date: Optional[str] = None

    deal_value_inr: Optional[int] = Field(
        default=None,
        ge=0
    )

    company_name: Optional[str] = None

    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0
    )

    @field_validator(
        "candidate_id",
        mode="before"
    )
    @classmethod
    def normalize_candidate_id(cls, value):

        return str(value).strip().lower()


# ============================================================
# TASK RESPONSE
# ============================================================

class TaskResponse(TaskCreate):

    id: int

    model_config = ConfigDict(
        from_attributes=True
    )


# ============================================================
# TASK UPDATE
# ============================================================

class TaskUpdate(BaseModel):

    title: Optional[str] = None
    description: Optional[str] = None

    assignee_id: Optional[Assignee] = None
    category: Optional[Category] = None
    priority: Optional[Priority] = None

    due_date: Optional[str] = None

    deal_value_inr: Optional[int] = Field(
        default=None,
        ge=0
    )

    company_name: Optional[str] = None

    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0
    )


# ============================================================
# EMAIL
# ============================================================

class Email(BaseModel):

    email_id: str
    thread_id: str

    message_index: int = 0

    from_name: str = ""

    from_email: EmailStr

    to: str = ""

    cc: list[str] = Field(
        default_factory=list
    )

    subject: str

    body: str

    received_at: str

    attachments: list[str] = Field(
        default_factory=list
    )

    is_reply: bool = False


# ============================================================
# INGEST REQUEST
# ============================================================

class IngestRequest(BaseModel):

    candidate_id: EmailStr

    emails: list[Email] = Field(
        ...,
        min_length=1,
        max_length=100
    )

    @field_validator(
        "candidate_id",
        mode="before"
    )
    @classmethod
    def normalize_candidate_id(cls, value):

        return str(value).strip().lower()