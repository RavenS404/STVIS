from __future__ import annotations

from datetime import UTC, datetime
import hashlib
from io import BytesIO
import os
from pathlib import Path
import uuid

from fastapi import HTTPException, UploadFile, status
from PIL import Image
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.ai_model import ModelProfile
from app.models.event import Event, EvidenceAsset, InferenceRun
from app.services.audit_service import record_audit
from app.services.inference_dispatcher import enqueue_event_processing
from app.services.object_storage import ObjectStorageService
from common.constants.enums import AssetKind, EventProcessingStatus, InferenceRunStatus, ModelKey


def _image_extension(content_type: str) -> str:
    return {
        "image/jpeg": ".jpg",
        "image/png": ".png",
        "image/webp": ".webp",
    }[content_type]


def _load_image(content: bytes) -> Image.Image:
    image = Image.open(BytesIO(content))
    image.load()
    return image.convert("RGB")


def _build_preview(image: Image.Image) -> bytes:
    preview = image.copy()
    preview.thumbnail((1280, 1280))
    output = BytesIO()
    preview.save(output, format="JPEG", quality=88)
    return output.getvalue()


def ingest_device_event(
    db: Session,
    *,
    device,
    upload: UploadFile,
    captured_at: datetime | None,
    external_ref: str | None,
    request_id: str | None,
    ip_address: str | None,
) -> tuple[Event, InferenceRun]:
    settings = get_settings()
    if upload.content_type not in settings.allowed_image_types:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported image type")

    content = upload.file.read()
    max_size_bytes = settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File is too large")

    try:
        image = _load_image(content)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or corrupted image file") from exc

    sha256 = hashlib.sha256(content).hexdigest()
    preview_bytes = _build_preview(image)
    storage = ObjectStorageService()
    storage.ensure_bucket()

    event = Event(
        external_ref=external_ref,
        device_id=device.id,
        ingest_source_ip=ip_address,
        captured_at=captured_at,
        received_at=datetime.now(UTC),
        processing_status=EventProcessingStatus.RECEIVED,
        evidence_sha256=sha256,
        mime_type=upload.content_type,
        file_size_bytes=len(content),
        image_width=image.size[0],
        image_height=image.size[1],
        event_metadata={"filename": upload.filename or "event-image"},
    )
    db.add(event)
    db.flush()

    extension = _image_extension(upload.content_type)
    original_key = f"events/{event.id}/original{extension}"
    preview_key = f"events/{event.id}/preview.jpg"
    storage.put_bytes(original_key, content, upload.content_type)
    storage.put_bytes(preview_key, preview_bytes, "image/jpeg")

    original_asset = EvidenceAsset(
        event_id=event.id,
        kind=AssetKind.ORIGINAL,
        bucket_name=storage.bucket,
        object_key=original_key,
        mime_type=upload.content_type,
        file_size_bytes=len(content),
        sha256=sha256,
        width=image.size[0],
        height=image.size[1],
    )
    preview_asset = EvidenceAsset(
        event_id=event.id,
        kind=AssetKind.PREVIEW,
        bucket_name=storage.bucket,
        object_key=preview_key,
        mime_type="image/jpeg",
        file_size_bytes=len(preview_bytes),
        sha256=hashlib.sha256(preview_bytes).hexdigest(),
        width=min(image.size[0], 1280),
        height=min(image.size[1], 1280),
    )
    db.add_all([original_asset, preview_asset])
    db.flush()

    event.original_asset_id = original_asset.id
    event.preview_asset_id = preview_asset.id

    violation_model = db.scalar(select(ModelProfile).where(ModelProfile.model_key == ModelKey.VIOLATION_DETECTION))
    plate_model = db.scalar(select(ModelProfile).where(ModelProfile.model_key == ModelKey.PLATE_DETECTION))
    if violation_model is None or plate_model is None:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Model profiles are not seeded")

    run = InferenceRun(
        event_id=event.id,
        status=InferenceRunStatus.QUEUED,
        violation_model_id=violation_model.id,
        plate_model_id=plate_model.id,
        violation_model_version=violation_model.version,
        plate_model_version=plate_model.version,
        raw_payload={},
        summary_payload={},
    )
    db.add(run)
    db.flush()

    task_id = None
    event.latest_run_id = run.id
    event.processing_status = EventProcessingStatus.QUEUED

    record_audit(
        db,
        actor_device_id=str(device.id),
        actor_role="device",
        action_type="event.ingested",
        entity_type="event",
        entity_id=str(event.id),
        summary_ar="تم استلام حدث جديد من الجهاز وإرساله للتحليل",
        summary_en="Event was received from device and queued for inference",
        request_id=request_id,
        ip_address=ip_address,
        details={
            "device_code": device.code,
            "sha256": sha256,
            "file_size_bytes": len(content),
            "task_id": task_id,
        },
    )
    db.flush()
    return event, run


def dispatch_ingest_inference(db: Session, *, event: Event, run: InferenceRun) -> str:
    task_id = enqueue_event_processing(str(event.id), str(run.id))
    run.task_id = task_id
    db.flush()
    return task_id
