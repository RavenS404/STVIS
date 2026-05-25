from __future__ import annotations

from datetime import UTC, datetime
import uuid

from celery.signals import heartbeat_sent, worker_ready
from PIL import Image, ImageEnhance, ImageFilter
from sqlalchemy import select

from app.models.ai_model import ModelProfile
from app.models.case import CasePlateRead, CaseViolation, VehicleCase
from app.models.event import Event, EvidenceAsset, InferenceRun
from app.models.monitoring import ServiceHeartbeat
from app.services.audit_service import record_audit
from app.services.object_storage import ObjectStorageService
from app.services.settings_service import get_settings_map, load_policy_settings
from app.db.session import SessionLocal
from common.constants.enums import AssetKind, CaseReviewState, DecisionSource, EventProcessingStatus, InferenceRunStatus
from common.constants.violation_catalog import VIOLATION_CATALOG
from common.utils.association import associate_entities
from common.utils.plate_reading import reconstruct_plate, serialize_plate_result
from common.utils.policy import ViolationSnapshot, evaluate_case_policy
from worker.app.celery_app import celery_app
from worker.app.inference.drawing import annotate_event, annotate_violations_only, crop_box, crop_driver_zoom
from worker.app.inference.model_runtime import runtime


def _upsert_heartbeat(service_name: str, status: str, payload: dict) -> None:
    with SessionLocal() as db:
        heartbeat = db.get(ServiceHeartbeat, service_name)
        if heartbeat is None:
            heartbeat = ServiceHeartbeat(
                service_name=service_name,
                status=status,
                last_seen_at=datetime.now(UTC),
                payload_json=payload,
            )
            db.add(heartbeat)
        else:
            heartbeat.status = status
            heartbeat.last_seen_at = datetime.now(UTC)
            heartbeat.payload_json = payload
        db.commit()


@worker_ready.connect
def on_worker_ready(**_kwargs):
    payload = runtime.warmup()
    _upsert_heartbeat("celery-worker", "ok", {"message": "worker is ready"})
    _upsert_heartbeat("model:violation_detection", "ok",
                      payload["violation_detection"])
    _upsert_heartbeat("model:plate_detection", "ok",
                      payload["plate_detection"])


@heartbeat_sent.connect
def on_worker_heartbeat(**_kwargs):
    _upsert_heartbeat("celery-worker", "ok", {"message": "heartbeat"})


def _case_number(event_id: uuid.UUID, ordinal: int) -> str:
    stamp = datetime.now(UTC).strftime("%Y%m%d")
    return f"ITVM-{stamp}-{str(event_id).split('-')[0].upper()}-{ordinal:02d}"


def _load_image_from_bytes(content: bytes) -> Image.Image:
    from io import BytesIO

    image = Image.open(BytesIO(content))
    image.load()
    return image.convert("RGB")


def _prepare_plate_crop_for_reading(plate_crop: Image.Image, *, scale_factor: int = 3) -> Image.Image:
    prepared = plate_crop.convert("RGB")
    prepared = prepared.resize(
        (max(prepared.width * scale_factor, 1), max(prepared.height * scale_factor, 1)),
        Image.Resampling.BICUBIC,
    )
    prepared = ImageEnhance.Contrast(prepared).enhance(1.18)
    prepared = ImageEnhance.Sharpness(prepared).enhance(1.35)
    return prepared.filter(ImageFilter.UnsharpMask(radius=1.1, percent=115, threshold=3))


def _store_asset(db, *, event_id, case_id, kind, bytes_content, mime_type, storage, object_key, sha256=None, size=None, width=None, height=None):
    storage.put_bytes(object_key, bytes_content, mime_type)
    asset = EvidenceAsset(
        event_id=event_id,
        case_id=case_id,
        kind=kind,
        bucket_name=storage.bucket,
        object_key=object_key,
        mime_type=mime_type,
        file_size_bytes=size or len(bytes_content),
        sha256=sha256,
        width=width,
        height=height,
    )
    db.add(asset)
    db.flush()
    return asset


@celery_app.task(name="worker.process_event")
def process_event(event_id: str, inference_run_id: str) -> dict:
    storage = ObjectStorageService()
    with SessionLocal() as db:
        event = db.get(Event, event_id)
        run = db.get(InferenceRun, inference_run_id)
        if event is None or run is None:
            return {"status": "missing"}

        try:
            settings_map = get_settings_map(db)
            policy_settings = load_policy_settings(db)
            run.status = InferenceRunStatus.RUNNING
            run.started_at = datetime.now(UTC)
            event.processing_status = EventProcessingStatus.PROCESSING
            db.flush()

            original_asset = event.original_asset
            original_bytes = storage.get_bytes(original_asset.object_key)
            image = _load_image_from_bytes(original_bytes)
            detections = runtime.detect_violations(image, max_det=int(
                settings_map["policy.max_detections_per_event"]))
            associations = associate_entities(
                detections,
                min_plate_score=float(
                    settings_map["association.min_plate_score"]),
                ambiguity_gap=float(settings_map["association.ambiguity_gap"]),
            )

            # Supersede previous active cases on rerun.
            for active_case in event.cases:
                active_case.is_active = False

            case_overlays: list[dict] = []
            cases_created = 0
            existing_case_total = len(event.cases)
            for index, association in enumerate(associations.vehicles, start=1):
                actionable_candidates = [
                    item
                    for item in association.violations
                    if item.label in VIOLATION_CATALOG and item.confidence >= float(settings_map["violation.min_confidence"])
                ]
                if not actionable_candidates and not association.flags:
                    continue
                case_ordinal = existing_case_total + cases_created + 1

                case = VehicleCase(
                    event_id=event.id,
                    inference_run_id=run.id,
                    case_number=_case_number(event.id, case_ordinal),
                    vehicle_index=index,
                    vehicle_label=association.vehicle.label,
                    vehicle_confidence=association.vehicle.confidence,
                    association_status=association.association_status,
                    vehicle_bbox={"bbox": list(association.vehicle.bbox)},
                    raw_debug_payload={
                        "association_flags": association.flags,
                        "vehicle": {
                            "label": association.vehicle.label,
                            "confidence": association.vehicle.confidence,
                            "bbox": list(association.vehicle.bbox),
                        },
                    },
                    review_flags=list(association.flags),
                    decision_source=DecisionSource.SYSTEM,
                )
                db.add(case)
                db.flush()

                vehicle_crop = crop_box(
                    image, association.vehicle.bbox, padding=12)
                vehicle_crop_key = f"events/{event.id}/cases/{case.id}/vehicle_crop.png"
                vehicle_asset = _store_asset(
                    db,
                    event_id=event.id,
                    case_id=case.id,
                    kind=AssetKind.VEHICLE_CROP,
                    bytes_content=_image_bytes(vehicle_crop),
                    mime_type="image/png",
                    storage=storage,
                    object_key=vehicle_crop_key,
                    width=vehicle_crop.width,
                    height=vehicle_crop.height,
                )
                _ = vehicle_asset

                plate_confidence = None
                if association.plate is not None:
                    plate_crop = crop_box(
                        image, association.plate.bbox, padding=8)
                    plate_crop = _prepare_plate_crop_for_reading(
                        plate_crop, scale_factor=3)
                    plate_token_detections = runtime.detect_plate_tokens(
                        plate_crop)
                    plate_result = reconstruct_plate(plate_token_detections)
                    plate_confidence = plate_result.plate_confidence

                    if "غير" in plate_result.display_summary_ar and "incomplete_plate_reading" not in association.flags:
                        association.flags.append("incomplete_plate_reading")

                    plate_crop_key = f"events/{event.id}/cases/{case.id}/plate_crop.png"
                    plate_asset = _store_asset(
                        db,
                        event_id=event.id,
                        case_id=case.id,
                        kind=AssetKind.PLATE_CROP,
                        bytes_content=_image_bytes(plate_crop),
                        mime_type="image/png",
                        storage=storage,
                        object_key=plate_crop_key,
                        width=plate_crop.width,
                        height=plate_crop.height,
                    )
                    _ = plate_asset
                    plate_payload = serialize_plate_result(plate_result)
                    db.add(
                        CasePlateRead(
                            case_id=case.id,
                            inference_run_id=run.id,
                            raw_text_visual=plate_payload["raw_text_visual"],
                            arabic_text_display=plate_payload["arabic_text_display"],
                            normalized_search_value=plate_payload["normalized_search_value"],
                            letters_ar=plate_payload["letters_ar"],
                            digits_ar=plate_payload["digits_ar"],
                            raw_letters=plate_payload["raw_letters"],
                            raw_digits=plate_payload["raw_digits"],
                            plate_confidence=plate_payload["plate_confidence"],
                            token_count=plate_payload["token_count"],
                            row_count=plate_payload["row_count"],
                            token_details=plate_payload["token_details"],
                            plate_bbox={"bbox": list(association.plate.bbox)},
                            raw_debug_payload={
                                "raw_token_detections": plate_token_detections},
                            model_version=runtime.plate_model.version,
                            association_score=association.plate_score,
                            is_confident=(
                                plate_payload["plate_confidence"] >= float(
                                    settings_map["plate.direct_issue_threshold"])
                                and "غير" not in plate_payload["display_summary_ar"]
                            ),
                        )
                    )
                    case.raw_debug_payload["plate_detection"] = {
                        "plate_bbox": list(association.plate.bbox),
                        "plate_result": plate_payload,
                        "raw_token_detections": plate_token_detections,
                    }

                violation_snapshots: list[ViolationSnapshot] = []
                for detection in actionable_candidates:
                    catalog = VIOLATION_CATALOG[detection.label]
                    review_required = detection.confidence < float(
                        settings_map["violation.direct_issue_threshold"])
                    violation = CaseViolation(
                        case_id=case.id,
                        inference_run_id=run.id,
                        code=catalog["code"],
                        display_name_ar=catalog["name_ar"],
                        display_name_en=catalog["name_en"],
                        confidence=detection.confidence,
                        actionable=bool(catalog["actionable"]),
                        review_required=review_required,
                        is_highlighted=False,
                        detection_bbox={"bbox": list(detection.bbox)},
                        raw_debug_payload={"source_label": detection.label},
                    )
                    db.add(violation)
                    case.violations.append(violation)
                    violation_snapshots.append(
                        ViolationSnapshot(code=catalog["code"], confidence=detection.confidence, actionable=bool(
                            catalog["actionable"]))
                    )

                decision = evaluate_case_policy(
                    violations=violation_snapshots,
                    plate_confidence=plate_confidence,
                    association_status=association.association_status,
                    flags=association.flags,
                    settings=policy_settings,
                )
                case.review_state = decision.review_state
                case.highlighted_violation_code = decision.highlighted_violation_code
                case.requires_supervisor = decision.requires_supervisor
                case.issue_ready = decision.review_state == CaseReviewState.DIRECT_ISSUE_READY
                case.review_flags = decision.review_flags
                if decision.review_state == CaseReviewState.ISSUED:
                    case.issued_at = datetime.now(UTC)

                for violation in case.violations:
                    violation.is_highlighted = violation.code == decision.highlighted_violation_code

                case_violation_detections = [
                    {
                        "label": detection.label,
                        "confidence": detection.confidence,
                        "bbox": list(detection.bbox),
                    }
                    for detection in actionable_candidates
                ]
                if case_violation_detections:
                    violations_annotated_bytes = annotate_violations_only(
                        image, case_violation_detections)
                    violations_annotated_key = f"events/{event.id}/cases/{case.id}/violations_annotated.jpg"
                    _store_asset(
                        db,
                        event_id=event.id,
                        case_id=case.id,
                        kind=AssetKind.VIOLATIONS_ANNOTATED,
                        bytes_content=violations_annotated_bytes,
                        mime_type="image/jpeg",
                        storage=storage,
                        object_key=violations_annotated_key,
                        width=image.width,
                        height=image.height,
                    )

                    driver_zoom = crop_driver_zoom(
                        image,
                        support_bbox=list(association.support_zone.bbox) if association.support_zone else None,
                        vehicle_bbox=list(association.vehicle.bbox),
                        violation_bboxes=[list(detection.bbox) for detection in actionable_candidates],
                    )
                    driver_zoom_key = f"events/{event.id}/cases/{case.id}/driver_zoom.png"
                    _store_asset(
                        db,
                        event_id=event.id,
                        case_id=case.id,
                        kind=AssetKind.DRIVER_ZOOM,
                        bytes_content=_image_bytes(driver_zoom),
                        mime_type="image/png",
                        storage=storage,
                        object_key=driver_zoom_key,
                        width=driver_zoom.width,
                        height=driver_zoom.height,
                    )

                case_overlays.append(
                    {"case_number": case.case_number, "vehicle_bbox": list(association.vehicle.bbox)})
                record_audit(
                    db,
                    actor_role="system",
                    action_type="case.generated",
                    entity_type="vehicle_case",
                    entity_id=str(case.id),
                    summary_ar="تم إنشاء حالة مركبة من نتائج الاستدلال",
                    summary_en="Vehicle case was created from inference results",
                    details={
                        "case_number": case.case_number,
                        "review_state": case.review_state.value,
                        "review_flags": case.review_flags,
                    },
                )
                cases_created += 1

            annotated_bytes = annotate_event(image, detections, case_overlays)
            annotated_key = f"events/{event.id}/runs/{run.id}/annotated_event.jpg"
            annotated_asset = _store_asset(
                db,
                event_id=event.id,
                case_id=None,
                kind=AssetKind.ANNOTATED_EVENT,
                bytes_content=annotated_bytes,
                mime_type="image/jpeg",
                storage=storage,
                object_key=annotated_key,
                width=image.width,
                height=image.height,
            )
            event.annotated_asset_id = annotated_asset.id
            event.processing_status = EventProcessingStatus.COMPLETED
            event.last_error = None

            run.status = InferenceRunStatus.SUCCEEDED
            run.completed_at = datetime.now(UTC)
            run.violation_model_version = runtime.violation_model.version
            run.plate_model_version = runtime.plate_model.version
            run.raw_payload = {
                "event_id": event_id,
                "detections": detections,
                "association_summary": {
                    "vehicle_count": len(associations.vehicles),
                    "unmatched_plates": [list(item.bbox) for item in associations.unmatched_plates],
                    "unmatched_violations": [list(item.bbox) for item in associations.unmatched_violations],
                },
            }
            run.summary_payload = {"cases_created": cases_created}

            record_audit(
                db,
                actor_role="system",
                action_type="event.processed",
                entity_type="event",
                entity_id=str(event.id),
                summary_ar="اكتمل تحليل الحدث وحفظ النتائج",
                summary_en="Event inference finished and results were stored",
                details={"cases_created": cases_created,
                         "run_id": str(run.id)},
            )
            db.commit()
            return {"status": "ok", "event_id": event_id, "cases_created": cases_created}
        except Exception as exc:
            db.rollback()
            with SessionLocal() as error_db:
                event = error_db.get(Event, event_id)
                run = error_db.get(InferenceRun, inference_run_id)
                if event is not None:
                    event.processing_status = EventProcessingStatus.FAILED
                    event.last_error = str(exc)
                if run is not None:
                    run.status = InferenceRunStatus.FAILED
                    run.completed_at = datetime.now(UTC)
                    run.error_message = str(exc)
                record_audit(
                    error_db,
                    actor_role="system",
                    action_type="event.failed",
                    entity_type="event",
                    entity_id=event_id,
                    summary_ar="فشل تحليل الحدث",
                    summary_en="Event inference failed",
                    details={"error": str(exc)},
                )
                error_db.commit()
            raise


def _image_bytes(image: Image.Image) -> bytes:
    from io import BytesIO

    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()
