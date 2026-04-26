from __future__ import annotations

from sqlalchemy import Boolean, Enum, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from common.constants.enums import ModelKey


class ModelProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "model_profiles"

    model_key: Mapped[ModelKey] = mapped_column(Enum(ModelKey, name="model_key"), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(150), nullable=False)
    artifact_path: Mapped[str] = mapped_column(String(255), nullable=False)
    version: Mapped[str] = mapped_column(String(120), nullable=False)
    class_map: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    inference_runs_violation = relationship(
        "InferenceRun",
        back_populates="violation_model",
        foreign_keys="InferenceRun.violation_model_id",
    )
    inference_runs_plate = relationship(
        "InferenceRun",
        back_populates="plate_model",
        foreign_keys="InferenceRun.plate_model_id",
    )
