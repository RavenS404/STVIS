from fastapi import APIRouter, Depends, Request

from app.api.deps import CurrentUser, DbSession, get_client_ip, get_request_id, require_roles
from app.models.user import User
from app.schemas.case import (
    CaseDecisionRequest,
    CaseDetail,
    CaseListResponse,
    CaseUpdateRequest,
    CaseViolationCreateRequest,
    CaseViolationUpdateRequest,
)
from app.schemas.common import MessageResponse, PageMeta
from app.services.case_service import (
    apply_case_decision,
    create_case_violation,
    delete_case_violation,
    dispatch_rerun_inference,
    get_case_detail,
    list_cases,
    rerun_event_inference,
    update_case,
    update_case_violation,
)
from common.constants.enums import UserRole

router = APIRouter()


@router.get("", response_model=CaseListResponse)
def cases_list(
    db: DbSession,
    _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR)),
    page: int = 1,
    page_size: int = 20,
    state: str | None = None,
    search: str | None = None,
    only_supervisor_queue: bool = False,
) -> CaseListResponse:
    items, total = list_cases(
        db,
        page=page,
        page_size=page_size,
        state=state,
        search=search,
        only_supervisor_queue=only_supervisor_queue,
    )
    return CaseListResponse(items=items, meta=PageMeta(page=page, page_size=page_size, total=total))


@router.get("/{case_id}", response_model=CaseDetail)
def case_detail(case_id: str, db: DbSession, _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR))) -> CaseDetail:
    return CaseDetail(**get_case_detail(db, case_id))


@router.patch("/{case_id}", response_model=MessageResponse)
def update_case_route(
    case_id: str,
    payload: CaseUpdateRequest,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(
        UserRole.ADMIN, UserRole.SUPERVISOR)),
) -> MessageResponse:
    update_case(
        db,
        case_id=case_id,
        user=current_user,
        payload=payload.dict(exclude_none=True),
        request_id=get_request_id(request),
        ip_address=get_client_ip(request),
    )
    db.commit()
    return MessageResponse(message="Case updated successfully")


@router.post("/{case_id}/decision", response_model=MessageResponse)
def case_decision(
    case_id: str,
    payload: CaseDecisionRequest,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(
        UserRole.ADMIN, UserRole.SUPERVISOR)),
) -> MessageResponse:
    apply_case_decision(
        db,
        case_id=case_id,
        user=current_user,
        decision=payload.decision,
        notes=payload.notes,
        plate_override_ar=payload.plate_override_ar,
        confirmed_violation_ids=payload.confirmed_violation_ids,
        request_id=get_request_id(request),
        ip_address=get_client_ip(request),
    )
    db.commit()
    return MessageResponse(message="Case updated successfully")


@router.post("/{case_id}/violations", response_model=MessageResponse)
def create_case_violation_route(
    case_id: str,
    payload: CaseViolationCreateRequest,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(
        UserRole.ADMIN, UserRole.SUPERVISOR)),
) -> MessageResponse:
    create_case_violation(
        db,
        case_id=case_id,
        user=current_user,
        payload=payload.dict(exclude_none=True),
        request_id=get_request_id(request),
        ip_address=get_client_ip(request),
    )
    db.commit()
    return MessageResponse(message="Violation created successfully")


@router.patch("/{case_id}/violations/{violation_id}", response_model=MessageResponse)
def update_case_violation_route(
    case_id: str,
    violation_id: str,
    payload: CaseViolationUpdateRequest,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(
        UserRole.ADMIN, UserRole.SUPERVISOR)),
) -> MessageResponse:
    update_case_violation(
        db,
        case_id=case_id,
        violation_id=violation_id,
        user=current_user,
        payload=payload.dict(exclude_none=True),
        request_id=get_request_id(request),
        ip_address=get_client_ip(request),
    )
    db.commit()
    return MessageResponse(message="Violation updated successfully")


@router.delete("/{case_id}/violations/{violation_id}", response_model=MessageResponse)
def delete_case_violation_route(
    case_id: str,
    violation_id: str,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(
        UserRole.ADMIN, UserRole.SUPERVISOR)),
) -> MessageResponse:
    delete_case_violation(
        db,
        case_id=case_id,
        violation_id=violation_id,
        user=current_user,
        request_id=get_request_id(request),
        ip_address=get_client_ip(request),
    )
    db.commit()
    return MessageResponse(message="Violation deleted successfully")


@router.post("/events/{event_id}/rerun", response_model=MessageResponse)
def rerun_event(
    event_id: str,
    request: Request,
    db: DbSession,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> MessageResponse:
    latest_run = rerun_event_inference(
        db,
        event_id=event_id,
        user=current_user,
        request_id=get_request_id(request),
        ip_address=get_client_ip(request),
    )
    db.commit()
    dispatch_rerun_inference(db, event_id=event_id, run=latest_run)
    db.commit()
    return MessageResponse(message="Event queued for reprocessing")
