from sqlalchemy import Column, Integer, String, Float, UniqueConstraint

from .database import Base


# ============================================================
# TASK
# ============================================================

class Task(Base):

    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    candidate_id = Column(
        String,
        nullable=False,
        index=True
    )

    source_email_id = Column(
        String,
        nullable=False,
        index=True
    )

    thread_id = Column(
        String,
        nullable=False,
        index=True
    )

    title = Column(
        String,
        nullable=False
    )

    description = Column(
        String,
        nullable=True
    )

    assignee_id = Column(
        String,
        nullable=False
    )

    category = Column(
        String,
        nullable=False
    )

    priority = Column(
        String,
        nullable=False
    )

    due_date = Column(
        String,
        nullable=True
    )

    deal_value_inr = Column(
        Integer,
        nullable=True
    )

    company_name = Column(
        String,
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=False
    )

    # One email should create only one task
    # for a candidate.
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "source_email_id",
            name="uq_task_candidate_email"
        ),
    )


# ============================================================
# PROCESSED EMAIL
# ============================================================

class ProcessedEmail(Base):

    __tablename__ = "processed_emails"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    candidate_id = Column(
        String,
        nullable=False,
        index=True
    )

    email_id = Column(
        String,
        nullable=False,
        index=True
    )

    thread_id = Column(
        String,
        nullable=False,
        index=True
    )

    decision = Column(
        String,
        nullable=False
    )

    category = Column(
        String,
        nullable=True
    )

    assignee_id = Column(
        String,
        nullable=True
    )

    confidence = Column(
        Float,
        nullable=True
    )

    reason = Column(
        String,
        nullable=True
    )

    created_at = Column(
        String,
        nullable=False
    )

    # IMPORTANT:
    # The same email_id may theoretically appear
    # under different candidates.
    #
    # Therefore uniqueness is:
    # candidate_id + email_id
    __table_args__ = (
        UniqueConstraint(
            "candidate_id",
            "email_id",
            name="uq_processed_candidate_email"
        ),
    )