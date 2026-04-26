from __future__ import annotations

from dataclasses import dataclass, field

from common.constants.enums import AssociationStatus, CaseReviewState


@dataclass(slots=True)
class PolicySettings:
    violation_min_confidence: float
    violation_review_threshold: float
    violation_direct_issue_threshold: float
    plate_min_confidence: float
    plate_direct_issue_threshold: float
    auto_issue_enabled: bool = False
    escalate_on_missing_plate: bool = True


@dataclass(slots=True)
class ViolationSnapshot:
    code: str
    confidence: float
    actionable: bool = True


@dataclass(slots=True)
class PolicyDecision:
    review_state: CaseReviewState
    highlighted_violation_code: str | None
    requires_supervisor: bool
    review_flags: list[str] = field(default_factory=list)


def evaluate_case_policy(
    *,
    violations: list[ViolationSnapshot],
    plate_confidence: float | None,
    association_status: AssociationStatus,
    flags: list[str],
    settings: PolicySettings,
) -> PolicyDecision:
    review_flags = list(flags)
    actionable = [item for item in violations if item.actionable and item.confidence >= settings.violation_min_confidence]
    highlighted = max(actionable, key=lambda item: item.confidence, default=None)

    for violation in actionable:
        if violation.confidence < settings.violation_review_threshold:
            review_flags.append(f"doubtful_violation:{violation.code}")
        elif violation.confidence < settings.violation_direct_issue_threshold:
            review_flags.append(f"review_violation:{violation.code}")

    if plate_confidence is None:
        if settings.escalate_on_missing_plate:
            review_flags.append("plate_missing")
    else:
        if plate_confidence < settings.plate_min_confidence:
            review_flags.append("plate_low_confidence")
        elif plate_confidence < settings.plate_direct_issue_threshold:
            review_flags.append("plate_review_threshold")

    if association_status != AssociationStatus.CONFIDENT:
        review_flags.append(f"association:{association_status.value}")

    if highlighted is None:
        review_flags.append("no_actionable_violation")

    escalation_flags = [f for f in review_flags if f != "no_actionable_violation"]
    requires_supervisor = bool(escalation_flags)

    if highlighted is None and not requires_supervisor:
        state = CaseReviewState.NO_VIOLATION
    elif not requires_supervisor and settings.auto_issue_enabled:
        state = CaseReviewState.ISSUED
    elif requires_supervisor:
        state = CaseReviewState.SUPERVISOR_REVIEW_REQUIRED
    else:
        state = CaseReviewState.DIRECT_ISSUE_READY

    return PolicyDecision(
        review_state=state,
        highlighted_violation_code=highlighted.code if highlighted else None,
        requires_supervisor=requires_supervisor,
        review_flags=sorted(set(review_flags)),
    )
