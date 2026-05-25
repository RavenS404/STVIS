from __future__ import annotations

from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.case import CaseViolation, VehicleCase
from common.constants.enums import CaseReviewState


def build_dashboard_summary(db: Session, *, queue_depth: int) -> dict:
    cases_by_state = {
        key: value
        for key, value in db.execute(
            select(VehicleCase.review_state, func.count(
                VehicleCase.id)).group_by(VehicleCase.review_state)
        ).all()
    }
    violations_by_code = {
        key: value
        for key, value in db.execute(
            select(CaseViolation.display_name_ar, func.count(
                CaseViolation.id)).group_by(CaseViolation.display_name_ar)
        ).all()
    }
    start_of_day = datetime.combine(
        date.today(), datetime.min.time(), tzinfo=UTC)
    issued_today = db.scalar(
        select(func.count(VehicleCase.id)).where(
            VehicleCase.review_state == CaseReviewState.ISSUED,
            VehicleCase.issued_at >= start_of_day,
        )
    ) or 0
    escalations = db.scalar(
        select(func.count(VehicleCase.id)).where(
            VehicleCase.review_state == CaseReviewState.SUPERVISOR_REVIEW_REQUIRED)
    ) or 0
    recent_cases = [
        {
            "id": str(row.id),
            "case_number": row.case_number,
            "state": row.review_state.value,
            "created_at": row.created_at.isoformat(),
        }
        for row in db.scalars(select(VehicleCase).order_by(VehicleCase.created_at.desc()).limit(8))
    ]

    return {
        "cases_by_state": {key.value if hasattr(key, "value") else str(key): value for key, value in cases_by_state.items()},
        "violations_by_code": violations_by_code,
        "queue_depth": queue_depth,
        "escalations": escalations,
        "issued_today": issued_today,
        "recent_cases": recent_cases,
    }
