from __future__ import annotations

from datetime import datetime
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from common.constants.enums import AssetKind, EventProcessingStatus, InferenceRunStatus


class Event(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "events"

    external_ref: Mapped[str | None] = mapped_column(String(120), nullable=True, unique=True)
    device_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("devices.id"), nullable=False, index=True)
    ingest_source_ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    processing_status: Mapped[EventProcessingStatus] = mapped_column(
        Enum(EventProcessingStatus, name="event_processing_status"),
        nullable=False,
        default=EventProcessingStatus.RECEIVED,
    )
    evidence_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    image_width: Mapped[int] = mapped_column(Integer, nullable=False)
    image_height: Mapped[int] = mapped_column(Integer, nullable=False)
    original_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("evidence_assets.id"), nullable=True)
    preview_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("evidence_assets.id"), nullable=True)
    annotated_asset_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("evidence_assets.id"), nullable=True)
    latest_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("inference_runs.id"), nullable=True)
    event_metadata: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    device = relationship("Device", back_populates="events")
    assets = relationship("EvidenceAsset", back_populates="event", foreign_keys="EvidenceAsset.event_id")
    original_asset = relationship("EvidenceAsset", foreign_keys=[original_asset_id], post_update=True)
    preview_asset = relationship("EvidenceAsset", foreign_keys=[preview_asset_id], post_update=True)
    annotated_asset = relationship("EvidenceAsset", foreign_keys=[annotated_asset_id], post_update=True)
    inference_runs = relationship("InferenceRun", back_populates="event", foreign_keys="InferenceRun.event_id")
    cases = relationship("VehicleCase", back_populates="event", foreign_keys="VehicleCase.event_id")


class EvidenceAsset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evidence_assets"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("vehicle_cases.id"), nullable=True, index=True)
    kind: Mapped[AssetKind] = mapped_column(Enum(AssetKind, name="asset_kind"), nullable=False)
    bucket_name: Mapped[str] = mapped_column(String(120), nullable=False)
    object_key: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)

    event = relationship("Event", back_populates="assets", foreign_keys=[event_id])
    case = relationship("VehicleCase", back_populates="assets", foreign_keys=[case_id])


class InferenceRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "inference_runs"

    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("events.id"), nullable=False, index=True)
    status: Mapped[InferenceRunStatus] = mapped_column(
        Enum(InferenceRunStatus, name="inference_run_status"),
        nullable=False,
        default=InferenceRunStatus.QUEUED,
    )
    task_id: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    violation_model_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("model_profiles.id"), nullable=True)
    plate_model_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("model_profiles.id"), nullable=True)
    violation_model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    plate_model_version: Mapped[str | None] = mapped_column(String(120), nullable=True)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    summary_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    event = relationship("Event", back_populates="inference_runs", foreign_keys=[event_id])
    violation_model = relationship("ModelProfile", back_populates="inference_runs_violation", foreign_keys=[violation_model_id])
    plate_model = relationship("ModelProfile", back_populates="inference_runs_plate", foreign_keys=[plate_model_id])
