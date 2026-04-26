from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import DbSession, require_roles
from app.schemas.report import ReportSummary
from app.services.report_service import build_report_summary, export_cases_csv
from common.constants.enums import UserRole

router = APIRouter()


@router.get("/summary", response_model=ReportSummary)
def reports_summary(db: DbSession, _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR))) -> ReportSummary:
    return ReportSummary(**build_report_summary(db))


@router.get("/export.csv")
def export_csv(db: DbSession, _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR))):
    csv_content = export_cases_csv(db)
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="stvis_cases.csv"'},
    )
