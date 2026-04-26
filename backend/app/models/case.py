from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, JSON, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from common.constants.enums import AssociationStatus, CaseReviewState, DecisionSource


class VehicleCase(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_cases"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    inference_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inference_runs.id"), nullable=False, index=True)
    case_number: Mapped[str] = mapped_column(String(40), unique=True, nullable=False, index=True)
    vehicle_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    vehicle_label: Mapped[str] = mapped_column(String(80), nullable=False)
    vehicle_confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    association_status: Mapped[AssociationStatus] = mapped_column(
        Enum(AssociationStatus, name="association_status"),
        nullable=False,
        default=AssociationStatus.CONFIDENT,
    )
    review_state: Mapped[CaseReviewState] = mapped_column(
        Enum(CaseReviewState, name="case_review_state"),
        nullable=False,
        default=CaseReviewState.SUPERVISOR_REVIEW_REQUIRED,
    )
    decision_source: Mapped[DecisionSource] = mapped_column(
        Enum(DecisionSource, name="decision_source"),
        nullable=False,
        default=DecisionSource.SYSTEM,
    )
    highlighted_violation_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    issue_ready: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    requires_supervisor: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    review_flags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    vehicle_bbox: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_debug_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    manual_override_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    supervisor_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    supervisor_decision_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    supervisor_decision_by_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    event = relationship("Event", back_populates="cases", foreign_keys=[event_id])
    inference_run = relationship("InferenceRun")
    plate_read = relationship("CasePlateRead", back_populates="case", uselist=False, cascade="all, delete-orphan")
    violations = relationship("CaseViolation", back_populates="case", cascade="all, delete-orphan")
    assets = relationship("EvidenceAsset", back_populates="case", foreign_keys="EvidenceAsset.case_id")
    issued_by = relationship("User", foreign_keys=[issued_by_id])
    rejected_by = relationship("User", foreign_keys=[rejected_by_id])
    supervisor_decision_by = relationship("User", foreign_keys=[supervisor_decision_by_id])


class CasePlateRead(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "case_plate_reads"

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_cases.id"), nullable=False, unique=True)
    inference_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inference_runs.id"), nullable=False)
    raw_text_visual: Mapped[str] = mapped_column(String(255), nullable=False)
    arabic_text_display: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    normalized_search_value: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    letters_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    digits_ar: Mapped[str] = mapped_column(String(120), nullable=False)
    raw_letters: Mapped[str] = mapped_column(String(120), nullable=False)
    raw_digits: Mapped[str] = mapped_column(String(120), nullable=False)
    plate_confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, nullable=False)
    token_details: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    plate_bbox: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_debug_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    model_version: Mapped[str] = mapped_column(String(120), nullable=False)
    association_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    is_confident: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")

    case = relationship("VehicleCase", back_populates="plate_read")
    inference_run = relationship("InferenceRun")


class CaseViolation(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "case_violations"

    case_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_cases.id"), nullable=False, index=True)
    inference_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("inference_runs.id"), nullable=False)
    code: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    display_name_ar: Mapped[str] = mapped_column(String(150), nullable=False)
    display_name_en: Mapped[str] = mapped_column(String(150), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    actionable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    review_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_highlighted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    detection_bbox: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    raw_debug_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    case = relationship("VehicleCase", back_populates="violations")
    inference_run = relationship("InferenceRun")
