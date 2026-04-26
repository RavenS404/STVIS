from common.constants.enums import CaseReviewState


DEFAULT_SYSTEM_SETTINGS = {
    "violation.min_confidence": 0.45,
    "violation.review_threshold": 0.65,
    "violation.direct_issue_threshold": 0.78,
    "plate.min_confidence": 0.4,
    "plate.direct_issue_threshold": 0.72,
    "association.min_plate_score": 0.35,
    "association.ambiguity_gap": 0.08,
    "ingest.max_upload_size_mb": 12,
    "policy.auto_issue_enabled": True,
    "policy.direct_issue_default_state": CaseReviewState.DIRECT_ISSUE_READY.value,
    "policy.escalate_on_ambiguous_association": True,
    "policy.escalate_on_missing_plate": True,
    "policy.max_detections_per_event": 24,
}
