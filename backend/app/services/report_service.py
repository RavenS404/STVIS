from __future__ import annotations

import csv
from io import StringIO

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.case import CasePlateRead, CaseViolation, VehicleCase
from common.constants.enums import CaseReviewState
from common.constants.violation_catalog import VIOLATION_CATALOG

CODE_TO_ARABIC = {item["code"]: item["name_ar"] for item in VIOLATION_CATALOG.values()}


def build_report_summary(db: Session) -> dict:
    total_cases = db.scalar(select(func.count(VehicleCase.id))) or 0
    issued_cases = db.scalar(select(func.count(VehicleCase.id)).where(VehicleCase.review_state == CaseReviewState.ISSUED)) or 0
    rejected_cases = db.scalar(select(func.count(VehicleCase.id)).where(VehicleCase.review_state == CaseReviewState.REJECTED)) or 0
    supervisor_cases = db.scalar(
        select(func.count(VehicleCase.id)).where(VehicleCase.review_state == CaseReviewState.SUPERVISOR_REVIEW_REQUIRED)
    ) or 0
    average_plate_confidence = db.scalar(select(func.avg(CasePlateRead.plate_confidence)))
    violation_breakdown = {
        code: count
        for code, count in db.execute(
            select(CaseViolation.display_name_ar, func.count(CaseViolation.id)).group_by(CaseViolation.display_name_ar)
        ).all()
    }

    return {
        "total_cases": total_cases,
        "issued_cases": issued_cases,
        "rejected_cases": rejected_cases,
        "supervisor_cases": supervisor_cases,
        "average_plate_confidence": float(average_plate_confidence) if average_plate_confidence is not None else None,
        "violation_breakdown": violation_breakdown,
    }


def export_cases_csv(db: Session) -> str:
    query = (
        select(VehicleCase, CasePlateRead)
        .outerjoin(CasePlateRead, CasePlateRead.case_id == VehicleCase.id)
        .order_by(VehicleCase.created_at.desc())
    )
    rows = db.execute(query).all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "case_number",
            "state",
            "highlighted_violation",
            "plate_ar",
            "plate_confidence",
            "requires_supervisor",
            "created_at",
        ]
    )
    for case, plate in rows:
        writer.writerow(
            [
                case.case_number,
                case.review_state.value,
                CODE_TO_ARABIC.get(case.highlighted_violation_code or "", case.highlighted_violation_code or ""),
                (f"{plate.letters_ar} {plate.digits_ar}".strip() or plate.arabic_text_display) if plate else "",
                float(plate.plate_confidence) if plate else "",
                case.requires_supervisor,
                case.created_at.isoformat(),
            ]
        )
    return output.getvalue()
