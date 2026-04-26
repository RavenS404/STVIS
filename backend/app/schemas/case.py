from __future__ import annotations

from pydantic import BaseModel

from app.schemas.common import PageMeta
from common.constants.enums import AssociationStatus, CaseReviewState


class CaseViolationRead(BaseModel):
    id: str
    code: str
    display_name_ar: str
    display_name_en: str
    confidence: float
    actionable: bool
    review_required: bool
    is_highlighted: bool
    detection_bbox: dict


class CasePlateReadSchema(BaseModel):
    id: str
    raw_text_visual: str
    arabic_text_display: str
    display_summary_ar: str
    normalized_search_value: str
    letters_ar: str
    digits_ar: str
    raw_letters: str
    raw_digits: str
    plate_confidence: float
    token_count: int
    row_count: int
    token_details: list[dict]
    plate_bbox: dict
    model_version: str
    association_score: float | None = None
    is_confident: bool


class CaseAssetRead(BaseModel):
    id: str
    kind: str
    mime_type: str
    url: str


class CaseListItem(BaseModel):
    id: str
    case_number: str
    review_state: CaseReviewState
    association_status: AssociationStatus
    highlighted_violation_code: str | None
    review_flags: list[str]
    issue_ready: bool
    requires_supervisor: bool
    vehicle_label: str
    vehicle_confidence: float
    event_id: str
    plate_text_ar: str | None = None
    plate_confidence: float | None = None
    violation_summary_ar: str | None = None
    created_at: str
    violations: list[CaseViolationRead]


class CaseListResponse(BaseModel):
    items: list[CaseListItem]
    meta: PageMeta


class CaseDetail(BaseModel):
    id: str
    case_number: str
    event_id: str
    review_state: CaseReviewState
    association_status: AssociationStatus
    highlighted_violation_code: str | None
    review_flags: list[str]
    issue_ready: bool
    requires_supervisor: bool
    vehicle_label: str
    vehicle_confidence: float
    vehicle_bbox: dict
    supervisor_notes: str | None
    manual_override_payload: dict
    plate_read: CasePlateReadSchema | None = None
    violations: list[CaseViolationRead]
    assets: list[CaseAssetRead]
    model_versions: dict
    debug_payload: dict
    created_at: str
    updated_at: str


class CaseDecisionRequest(BaseModel):
    decision: str
    notes: str | None = None
    plate_override_ar: str | None = None
    confirmed_violation_ids: list[str] | None = None


class CaseFilters(BaseModel):
    state: str | None = None
    search: str | None = None
    only_supervisor_queue: bool = False
