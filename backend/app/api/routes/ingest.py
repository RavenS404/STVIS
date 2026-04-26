from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from app.api.deps import DbSession, authenticate_device, get_client_ip, get_request_id
from app.schemas.ingest import IngestEventResponse
from app.services.event_ingest_service import dispatch_ingest_inference, ingest_device_event

router = APIRouter()


@router.post("/events", response_model=IngestEventResponse)
def ingest_event(
    request: Request,
    db: DbSession,
    device=Depends(authenticate_device),
    evidence: UploadFile = File(...),
    captured_at: datetime | None = Form(default=None),
    external_ref: str | None = Form(default=None),
) -> IngestEventResponse:
    event, run = ingest_device_event(
        db,
        device=device,
        upload=evidence,
        captured_at=captured_at,
        external_ref=external_ref,
        request_id=get_request_id(request),
        ip_address=get_client_ip(request),
    )
    db.commit()
    dispatch_ingest_inference(db, event=event, run=run)
    db.commit()
    return IngestEventResponse(event_id=str(event.id), status=event.processing_status.value)
