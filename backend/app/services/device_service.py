from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import generate_device_token, hash_secret, verify_secret
from app.models.device import Device


def list_devices(db: Session) -> list[Device]:
    return list(db.scalars(select(Device).order_by(Device.created_at.desc())))


def create_device(db: Session, *, code: str, name: str, location_label: str, notes: str | None, metadata_json: dict) -> tuple[Device, str]:
    plain_token = generate_device_token()
    device = Device(
        code=code,
        name=name,
        location_label=location_label,
        notes=notes,
        metadata_json=metadata_json,
        hashed_token=hash_secret(plain_token),
    )
    db.add(device)
    db.flush()
    return device, plain_token


def verify_device_token(db: Session, code: str, token: str) -> Device | None:
    device = db.scalar(select(Device).where(Device.code == code, Device.is_active.is_(True)))
    if not device:
        return None
    if not verify_secret(token, device.hashed_token):
        return None
    device.last_seen_at = datetime.now(UTC)
    db.flush()
    return device


def rotate_device_token(db: Session, device: Device) -> str:
    plain_token = generate_device_token()
    device.hashed_token = hash_secret(plain_token)
    db.flush()
    return plain_token
