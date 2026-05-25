from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.config import get_settings
from app.models.case import CasePlateRead, CaseViolation, VehicleCase
from app.models.event import EvidenceAsset, Event, InferenceRun
from app.services.audit_service import record_audit
from app.services.inference_dispatcher import enqueue_event_processing
from common.constants.enums import CaseReviewState, DecisionSource, EventProcessingStatus, InferenceRunStatus


VALID_CASE_STATUS_UPDATES = {"valid", "invalid"}
ARABIC_DIGITS = "٠١٢٣٤٥٦٧٨٩"
EASTERN_ARABIC_DIGIT_MAP = str.maketrans("۰۱۲۳۴۵۶۷۸۹", ARABIC_DIGITS)
WESTERN_DIGIT_MAP = str.maketrans("0123456789", ARABIC_DIGITS)


def _to_float(value: Decimal | float | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _asset_url(asset: EvidenceAsset) -> str:
    settings = get_settings()
    return f"{settings.api_v1_prefix}/evidence/assets/{asset.id}"


def _normalize_plate_override(value: str) -> tuple[str, str, str]:
    normalized = str(value).translate(EASTERN_ARABIC_DIGIT_MAP).translate(WESTERN_DIGIT_MAP)
    chars = [char for char in normalized if not char.isspace()]
    letters = "".join(char for char in chars if char not in ARABIC_DIGITS)
    digits = "".join(char for char in chars if char in ARABIC_DIGITS)
    search_value = "".join(chars)
    return letters, digits, search_value


def _violation_payload(item: CaseViolation) -> dict[str, Any]:
    return {
        "id": str(item.id),
        "code": item.code,
        "display_name_ar": item.display_name_ar,
        "display_name_en": item.display_name_en,
        "confidence": _to_float(item.confidence) or 0.0,
        "actionable": item.actionable,
        "review_required": item.review_required,
        "is_highlighted": item.is_highlighted,
        "detection_bbox": item.detection_bbox,
    }


def _plate_payload(item: CasePlateRead | None) -> dict[str, Any] | None:
    if item is None:
        return None

    reconstructed_summary = f"{item.letters_ar} {item.digits_ar}".strip()
    if item.normalized_search_value in {"LOW_CONFIDENCE", "INCOMPLETE", "UNKNOWN_CLASS_DETECTED"}:
        display_summary_ar = item.arabic_text_display
    elif not item.letters_ar or not item.digits_ar:
        display_summary_ar = item.arabic_text_display
    else:
        display_summary_ar = reconstructed_summary or item.arabic_text_display

    return {
        "id": str(item.id),
        "raw_text_visual": item.raw_text_visual,
        "arabic_text_display": item.arabic_text_display,
        "display_summary_ar": display_summary_ar,
        "normalized_search_value": item.normalized_search_value,
        "letters_ar": item.letters_ar,
        "digits_ar": item.digits_ar,
        "raw_letters": item.raw_letters,
        "raw_digits": item.raw_digits,
        "plate_confidence": _to_float(item.plate_confidence) or 0.0,
        "token_count": item.token_count,
        "row_count": item.row_count,
        "token_details": item.token_details,
        "plate_bbox": item.plate_bbox,
        "model_version": item.model_version,
        "association_score": _to_float(item.association_score),
        "is_confident": item.is_confident,
    }


def list_cases(
    db: Session,
    *,
    page: int,
    page_size: int,
    state: str | None,
    search: str | None,
    only_supervisor_queue: bool,
) -> tuple[list[dict], int]:
    filters = [VehicleCase.is_active.is_(True)]
    if only_supervisor_queue:
        filters.append(VehicleCase.review_state ==
                       CaseReviewState.SUPERVISOR_REVIEW_REQUIRED)
    elif state:
        filters.append(VehicleCase.review_state == state)

    if search:
        filters.append(
            or_(
                VehicleCase.case_number.ilike(f"%{search}%"),
                CasePlateRead.normalized_search_value.ilike(f"%{search}%"),
                CasePlateRead.arabic_text_display.ilike(f"%{search}%"),
            )
        )

    total = db.scalar(
        select(func.count(VehicleCase.id))
        .select_from(VehicleCase)
        .outerjoin(CasePlateRead)
        .where(*filters)
    ) or 0

    query = (
        select(VehicleCase)
        .outerjoin(CasePlateRead)
        .where(*filters)
        .options(selectinload(VehicleCase.plate_read), selectinload(VehicleCase.violations))
        .order_by(VehicleCase.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = list(db.scalars(query).unique())

    payload = []
    for item in items:
        plate_payload = _plate_payload(item.plate_read)
        violation_summary_ar = "، ".join(dict.fromkeys(
            violation.display_name_ar for violation in item.violations if violation.actionable))
        payload.append(
            {
                "id": str(item.id),
                "case_number": item.case_number,
                "review_state": item.review_state,
                "association_status": item.association_status,
                "highlighted_violation_code": item.highlighted_violation_code,
                "review_flags": item.review_flags,
                "issue_ready": item.issue_ready,
                "requires_supervisor": item.requires_supervisor,
                "vehicle_label": item.vehicle_label,
                "vehicle_confidence": _to_float(item.vehicle_confidence) or 0.0,
                "event_id": str(item.event_id),
                "plate_text_ar": plate_payload["display_summary_ar"] if plate_payload else None,
                "plate_letters_ar": plate_payload["letters_ar"] if plate_payload else None,
                "plate_digits_ar": plate_payload["digits_ar"] if plate_payload else None,
                "plate_confidence": plate_payload["plate_confidence"] if plate_payload else None,
                "violation_summary_ar": violation_summary_ar or None,
                "created_at": item.created_at.isoformat(),
                "violations": [_violation_payload(violation) for violation in item.violations],
            }
        )
    return payload, total


def get_case_detail(db: Session, case_id: str) -> dict[str, Any]:
    case = db.scalar(
        select(VehicleCase)
        .where(VehicleCase.id == case_id)
        .options(
            selectinload(VehicleCase.plate_read),
            selectinload(VehicleCase.violations),
            selectinload(VehicleCase.assets),
            joinedload(VehicleCase.event).joinedload(Event.original_asset),
            joinedload(VehicleCase.event).joinedload(Event.preview_asset),
            joinedload(VehicleCase.event).joinedload(Event.annotated_asset),
            joinedload(VehicleCase.inference_run),
        )
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    assets = [
        {"id": str(asset.id), "kind": asset.kind.value,
         "mime_type": asset.mime_type, "url": _asset_url(asset)}
        for asset in case.assets
    ]
    for event_asset in [case.event.original_asset, case.event.preview_asset, case.event.annotated_asset]:
        if event_asset:
            assets.append(
                {
                    "id": str(event_asset.id),
                    "kind": event_asset.kind.value,
                    "mime_type": event_asset.mime_type,
                    "url": _asset_url(event_asset),
                }
            )
    return {
        "id": str(case.id),
        "case_number": case.case_number,
        "event_id": str(case.event_id),
        "review_state": case.review_state,
        "association_status": case.association_status,
        "highlighted_violation_code": case.highlighted_violation_code,
        "review_flags": case.review_flags,
        "issue_ready": case.issue_ready,
        "requires_supervisor": case.requires_supervisor,
        "vehicle_label": case.vehicle_label,
        "vehicle_confidence": _to_float(case.vehicle_confidence) or 0.0,
        "vehicle_bbox": case.vehicle_bbox,
        "supervisor_notes": case.supervisor_notes,
        "manual_override_payload": case.manual_override_payload,
        "plate_read": _plate_payload(case.plate_read),
        "violations": [_violation_payload(item) for item in case.violations],
        "violation_summary_ar": "، ".join(dict.fromkeys(item.display_name_ar for item in case.violations if item.actionable)),
        "assets": assets,
        "model_versions": {
            "violation_model": case.inference_run.violation_model_version if case.inference_run else None,
            "plate_model": case.inference_run.plate_model_version if case.inference_run else None,
        },
        "debug_payload": case.raw_debug_payload,
        "created_at": case.created_at.isoformat(),
        "updated_at": case.updated_at.isoformat(),
    }


def apply_case_decision(
    db: Session,
    *,
    case_id: str,
    user,
    decision: str,
    notes: str | None,
    plate_override_ar: str | None,
    confirmed_violation_ids: list[str] | None,
    request_id: str | None,
    ip_address: str | None,
) -> VehicleCase:
    case = db.scalar(
        select(VehicleCase)
        .where(VehicleCase.id == case_id)
        .options(selectinload(VehicleCase.plate_read))
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    case.supervisor_notes = notes or case.supervisor_notes
    if plate_override_ar:
        letters_ar, digits_ar, normalized_plate = _normalize_plate_override(plate_override_ar)
        display_plate = " ".join(part for part in [letters_ar, digits_ar] if part)
        case.manual_override_payload["plate_override_ar"] = display_plate or plate_override_ar
        if case.plate_read is not None:
            case.plate_read.arabic_text_display = display_plate or plate_override_ar
            case.plate_read.letters_ar = letters_ar
            case.plate_read.digits_ar = digits_ar
            case.plate_read.normalized_search_value = normalized_plate
    if confirmed_violation_ids:
        case.manual_override_payload["confirmed_violation_ids"] = confirmed_violation_ids

    now = datetime.now(UTC)
    if decision == "issue":
        case.review_state = CaseReviewState.ISSUED
        case.issue_ready = False
        case.requires_supervisor = False
        case.issued_at = now
        case.issued_by_id = user.id
    elif decision == "reject":
        case.review_state = CaseReviewState.REJECTED
        case.issue_ready = False
        case.rejected_at = now
        case.rejected_by_id = user.id
    elif decision == "mark_direct_ready":
        case.review_state = CaseReviewState.DIRECT_ISSUE_READY
        case.issue_ready = True
        case.requires_supervisor = False
    elif decision == "send_to_supervisor":
        case.review_state = CaseReviewState.SUPERVISOR_REVIEW_REQUIRED
        case.issue_ready = False
        case.requires_supervisor = True
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported case decision")

    case.supervisor_decision_at = now
    case.supervisor_decision_by_id = user.id
    case.decision_source = DecisionSource.ADMIN if user.role.value == "admin" else DecisionSource.SUPERVISOR

    record_audit(
        db,
        actor_user_id=str(user.id),
        actor_role=user.role.value,
        action_type=f"case.{decision}",
        entity_type="vehicle_case",
        entity_id=str(case.id),
        summary_ar="تم اتخاذ قرار على الحالة",
        summary_en="A case decision was applied",
        request_id=request_id,
        ip_address=ip_address,
        details={"decision": decision, "notes": notes},
    )
    db.flush()
    return case


def update_case(
    db: Session,
    *,
    case_id: str,
    user,
    payload: dict[str, Any],
    request_id: str | None,
    ip_address: str | None,
) -> VehicleCase:
    case = db.scalar(
        select(VehicleCase)
        .where(VehicleCase.id == case_id)
        .options(selectinload(VehicleCase.plate_read))
    )
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    plate_override_ar = payload.get("plate_override_ar")
    if plate_override_ar is not None:
        letters_ar, digits_ar, normalized_plate = _normalize_plate_override(plate_override_ar)
        display_plate = " ".join(part for part in [letters_ar, digits_ar] if part)
        case.manual_override_payload = {
            **(case.manual_override_payload or {}),
            "plate_override_ar": display_plate or plate_override_ar,
        }
        if case.plate_read is not None:
            case.plate_read.arabic_text_display = display_plate or plate_override_ar
            case.plate_read.letters_ar = letters_ar
            case.plate_read.digits_ar = digits_ar
            case.plate_read.normalized_search_value = normalized_plate

    if payload.get("notes") is not None:
        case.supervisor_notes = payload["notes"]

    requested_status = payload.get("status")
    if requested_status is not None:
        if requested_status not in VALID_CASE_STATUS_UPDATES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported case status")
        now = datetime.now(UTC)
        case.supervisor_decision_at = now
        case.supervisor_decision_by_id = user.id
        case.decision_source = DecisionSource.ADMIN if user.role.value == "admin" else DecisionSource.SUPERVISOR
        if requested_status == "valid":
            case.review_state = CaseReviewState.ISSUED
            case.issue_ready = False
            case.requires_supervisor = False
            case.issued_at = now
            case.issued_by_id = user.id
        else:
            case.review_state = CaseReviewState.NO_VIOLATION
            case.issue_ready = False
            case.requires_supervisor = False
            case.rejected_at = now
            case.rejected_by_id = user.id

    record_audit(
        db,
        actor_user_id=str(user.id),
        actor_role=user.role.value,
        action_type="case.updated",
        entity_type="vehicle_case",
        entity_id=str(case.id),
        summary_ar="تم تعديل بيانات الحالة",
        summary_en="Case data was updated",
        request_id=request_id,
        ip_address=ip_address,
        details={"payload": payload},
    )
    db.flush()
    return case


def create_case_violation(
    db: Session,
    *,
    case_id: str,
    user,
    payload: dict[str, Any],
    request_id: str | None,
    ip_address: str | None,
) -> CaseViolation:
    case = db.get(VehicleCase, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    violation = CaseViolation(
        case_id=case.id,
        inference_run_id=case.inference_run_id,
        code=payload["code"],
        display_name_ar=payload["display_name_ar"],
        display_name_en=payload["display_name_en"],
        confidence=payload.get("confidence") or 1.0,
        actionable=payload.get("actionable", True),
        review_required=payload.get("review_required", False),
        is_highlighted=payload.get("is_highlighted", False),
        detection_bbox={},
        raw_debug_payload={"source": "manual"},
    )
    db.add(violation)
    if violation.is_highlighted:
        case.highlighted_violation_code = violation.code
    db.flush()

    record_audit(
        db,
        actor_user_id=str(user.id),
        actor_role=user.role.value,
        action_type="case.violation_created",
        entity_type="case_violation",
        entity_id=str(violation.id),
        summary_ar="تم إضافة مخالفة للحالة",
        summary_en="A case violation was added",
        request_id=request_id,
        ip_address=ip_address,
        details={"payload": payload},
    )
    return violation


def update_case_violation(
    db: Session,
    *,
    case_id: str,
    violation_id: str,
    user,
    payload: dict[str, Any],
    request_id: str | None,
    ip_address: str | None,
) -> CaseViolation:
    violation = db.get(CaseViolation, violation_id)
    if violation is None or str(violation.case_id) != case_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    case = db.get(VehicleCase, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    original_code = violation.code
    if payload.get("code") is not None:
        violation.code = payload["code"]
    if payload.get("display_name_ar") is not None:
        violation.display_name_ar = payload["display_name_ar"]
    if payload.get("display_name_en") is not None:
        violation.display_name_en = payload["display_name_en"]
    if payload.get("confidence") is not None:
        violation.confidence = payload["confidence"]
    if payload.get("actionable") is not None:
        violation.actionable = payload["actionable"]
    if payload.get("review_required") is not None:
        violation.review_required = payload["review_required"]
    if payload.get("is_highlighted") is not None:
        violation.is_highlighted = payload["is_highlighted"]
        if violation.is_highlighted:
            case.highlighted_violation_code = violation.code
        elif case.highlighted_violation_code == original_code:
            case.highlighted_violation_code = None

    if payload.get("code") is not None and case.highlighted_violation_code == original_code:
        case.highlighted_violation_code = violation.code

    record_audit(
        db,
        actor_user_id=str(user.id),
        actor_role=user.role.value,
        action_type="case.violation_updated",
        entity_type="case_violation",
        entity_id=str(violation.id),
        summary_ar="تم تعديل بيانات المخالفة",
        summary_en="Case violation was updated",
        request_id=request_id,
        ip_address=ip_address,
        details={"payload": payload},
    )
    db.flush()
    return violation


def delete_case_violation(
    db: Session,
    *,
    case_id: str,
    violation_id: str,
    user,
    request_id: str | None,
    ip_address: str | None,
) -> None:
    violation = db.get(CaseViolation, violation_id)
    if violation is None or str(violation.case_id) != case_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Violation not found")

    case = db.get(VehicleCase, case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Case not found")

    if case.highlighted_violation_code == violation.code:
        case.highlighted_violation_code = None

    db.delete(violation)
    record_audit(
        db,
        actor_user_id=str(user.id),
        actor_role=user.role.value,
        action_type="case.violation_deleted",
        entity_type="case_violation",
        entity_id=str(violation.id),
        summary_ar="تم حذف مخالفة من الحالة",
        summary_en="A case violation was removed",
        request_id=request_id,
        ip_address=ip_address,
        details={"case_id": case_id},
    )
    db.flush()


def rerun_event_inference(db: Session, *, event_id: str, user, request_id: str | None, ip_address: str | None) -> InferenceRun:
    event = db.get(Event, event_id)
    if event is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    run = InferenceRun(
        event_id=event.id,
        status=InferenceRunStatus.QUEUED,
        violation_model_version=event.inference_runs[-1].violation_model_version if event.inference_runs else None,
        plate_model_version=event.inference_runs[-1].plate_model_version if event.inference_runs else None,
        raw_payload={},
        summary_payload={"rerun": True},
    )
    db.add(run)
    db.flush()
    task_id = None
    event.latest_run_id = run.id
    event.processing_status = EventProcessingStatus.QUEUED
    record_audit(
        db,
        actor_user_id=str(user.id),
        actor_role=user.role.value,
        action_type="event.rerun",
        entity_type="event",
        entity_id=str(event.id),
        summary_ar="تمت إعادة جدولة الحدث للتحليل",
        summary_en="Event was queued again for inference",
        request_id=request_id,
        ip_address=ip_address,
        details={"task_id": task_id},
    )
    db.flush()
    return run


def dispatch_rerun_inference(db: Session, *, event_id: str, run: InferenceRun) -> str:
    task_id = enqueue_event_processing(event_id, str(run.id))
    run.task_id = task_id
    db.flush()
    return task_id
