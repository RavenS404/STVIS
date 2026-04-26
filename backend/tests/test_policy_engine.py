from common.constants.enums import AssociationStatus, CaseReviewState
from common.utils.policy import PolicySettings, ViolationSnapshot, evaluate_case_policy


def _settings(**overrides):
    base = PolicySettings(
        violation_min_confidence=0.45,
        violation_review_threshold=0.65,
        violation_direct_issue_threshold=0.82,
        plate_min_confidence=0.55,
        plate_direct_issue_threshold=0.8,
        auto_issue_enabled=False,
    )
    for key, value in overrides.items():
        setattr(base, key, value)
    return base


def test_policy_allows_direct_issue_ready_for_confident_clean_case():
    decision = evaluate_case_policy(
        violations=[ViolationSnapshot(code="using_mobile", confidence=0.91)],
        plate_confidence=0.88,
        association_status=AssociationStatus.CONFIDENT,
        flags=[],
        settings=_settings(),
    )

    assert decision.review_state == CaseReviewState.DIRECT_ISSUE_READY
    assert decision.highlighted_violation_code == "using_mobile"
    assert decision.requires_supervisor is False


def test_policy_escalates_when_one_of_multiple_violations_is_doubtful():
    decision = evaluate_case_policy(
        violations=[
            ViolationSnapshot(code="using_mobile", confidence=0.9),
            ViolationSnapshot(code="wrong_way", confidence=0.58),
        ],
        plate_confidence=0.9,
        association_status=AssociationStatus.CONFIDENT,
        flags=[],
        settings=_settings(),
    )

    assert decision.review_state == CaseReviewState.SUPERVISOR_REVIEW_REQUIRED
    assert decision.requires_supervisor is True
    assert "doubtful_violation:wrong_way" in decision.review_flags


def test_policy_can_auto_issue_when_enabled_and_case_is_clean():
    decision = evaluate_case_policy(
        violations=[ViolationSnapshot(code="using_mobile", confidence=0.94)],
        plate_confidence=0.9,
        association_status=AssociationStatus.CONFIDENT,
        flags=[],
        settings=_settings(auto_issue_enabled=True),
    )

    assert decision.review_state == CaseReviewState.ISSUED
