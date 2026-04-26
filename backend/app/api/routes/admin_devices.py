from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import DbSession, require_roles
from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceRead, DeviceTokenResponse, DeviceUpdate
from app.services.device_service import create_device, list_devices, rotate_device_token
from common.constants.enums import UserRole

router = APIRouter()


@router.get("", response_model=list[DeviceRead])
def devices_list(db: DbSession, _user=Depends(require_roles(UserRole.ADMIN))):
    return [
        DeviceRead(
            id=str(item.id),
            code=item.code,
            name=item.name,
            location_label=item.location_label,
            is_active=item.is_active,
            last_seen_at=item.last_seen_at.isoformat() if item.last_seen_at else None,
            notes=item.notes,
            metadata_json=item.metadata_json,
        )
        for item in list_devices(db)
    ]


@router.post("", response_model=DeviceTokenResponse)
def devices_create(payload: DeviceCreate, db: DbSession, _user=Depends(require_roles(UserRole.ADMIN))):
    device, plain_token = create_device(
        db,
        code=payload.code,
        name=payload.name,
        location_label=payload.location_label,
        notes=payload.notes,
        metadata_json=payload.metadata_json,
    )
    db.commit()
    return DeviceTokenResponse(
        device=DeviceRead(
            id=str(device.id),
            code=device.code,
            name=device.name,
            location_label=device.location_label,
            is_active=device.is_active,
            last_seen_at=device.last_seen_at.isoformat() if device.last_seen_at else None,
            notes=device.notes,
            metadata_json=device.metadata_json,
        ),
        plain_token=plain_token,
    )


@router.patch("/{device_id}", response_model=DeviceRead)
def devices_update(device_id: str, payload: DeviceUpdate, db: DbSession, _user=Depends(require_roles(UserRole.ADMIN))):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(device, field, value)
    db.commit()
    return DeviceRead(
        id=str(device.id),
        code=device.code,
        name=device.name,
        location_label=device.location_label,
        is_active=device.is_active,
        last_seen_at=device.last_seen_at.isoformat() if device.last_seen_at else None,
        notes=device.notes,
        metadata_json=device.metadata_json,
    )


@router.post("/{device_id}/rotate-token", response_model=DeviceTokenResponse)
def devices_rotate_token(device_id: str, db: DbSession, _user=Depends(require_roles(UserRole.ADMIN))):
    device = db.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    plain_token = rotate_device_token(db, device)
    db.commit()
    return DeviceTokenResponse(
        device=DeviceRead(
            id=str(device.id),
            code=device.code,
            name=device.name,
            location_label=device.location_label,
            is_active=device.is_active,
            last_seen_at=device.last_seen_at.isoformat() if device.last_seen_at else None,
            notes=device.notes,
            metadata_json=device.metadata_json,
        ),
        plain_token=plain_token,
    )
