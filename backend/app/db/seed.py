from __future__ import annotations

from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_secret
from app.db.session import SessionLocal
from app.models.ai_model import ModelProfile
from app.models.device import Device
from app.models.setting import SystemSetting
from app.models.user import User
from common.constants.enums import ModelKey, UserRole
from common.constants.settings import DEFAULT_SYSTEM_SETTINGS


def _model_version(path: Path) -> str:
    stat = path.stat()
    return f"{path.name}:{int(stat.st_mtime)}"


def seed() -> None:
    settings = get_settings()
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.username == settings.default_admin_username))
        if admin is None:
            db.add(
                User(
                    username=settings.default_admin_username,
                    full_name="مدير النظام",
                    role=UserRole.ADMIN,
                    password_hash=hash_secret(settings.default_admin_password),
                )
            )

        supervisor = db.scalar(select(User).where(User.username == settings.default_supervisor_username))
        if supervisor is None:
            db.add(
                User(
                    username=settings.default_supervisor_username,
                    full_name="مشرف العمليات",
                    role=UserRole.SUPERVISOR,
                    password_hash=hash_secret(settings.default_supervisor_password),
                )
            )

        for key, value in DEFAULT_SYSTEM_SETTINGS.items():
            existing = db.get(SystemSetting, key)
            if existing is None:
                db.add(SystemSetting(key=key, value_json=value))

        violation_model_path = Path(settings.violation_model_path)
        plate_model_path = Path(settings.plate_model_path)
        model_seeds = [
            {
                "model_key": ModelKey.VIOLATION_DETECTION,
                "display_name": "Violation detection",
                "artifact_path": str(violation_model_path),
                "version": _model_version(violation_model_path),
                "class_map": {
                    "0": "car windshield",
                    "1": "car_plate",
                    "2": "seat-belt",
                    "3": "un seat-belt",
                    "4": "using_mobile",
                    "5": "vehicle",
                    "6": "wrong_way",
                },
            },
            {
                "model_key": ModelKey.PLATE_DETECTION,
                "display_name": "Plate token detection",
                "artifact_path": str(plate_model_path),
                "version": _model_version(plate_model_path),
                "class_map": {
                    "0": "1",
                    "1": "2",
                    "2": "3",
                    "3": "4",
                    "4": "5",
                    "5": "6",
                    "6": "7",
                    "7": "8",
                    "8": "9",
                    "9": "alf",
                    "10": "ba2",
                    "11": "dal",
                    "12": "ein",
                    "13": "fa2",
                    "14": "gem",
                    "15": "ha",
                    "16": "ha2",
                    "17": "lam",
                    "18": "mem",
                    "19": "non",
                    "20": "qaf",
                    "21": "ra2",
                    "22": "sad",
                    "23": "sen",
                    "24": "ta2",
                    "25": "waw",
                    "26": "ya2",
                },
            },
        ]
        for seed_item in model_seeds:
            existing = db.scalar(select(ModelProfile).where(ModelProfile.model_key == seed_item["model_key"]))
            if existing is None:
                db.add(ModelProfile(metadata_json={}, is_active=True, **seed_item))

        device = db.scalar(select(Device).where(Device.code == settings.demo_device_code))
        if device is None:
            db.add(
                Device(
                    code=settings.demo_device_code,
                    name=settings.demo_device_name,
                    location_label="تقاطع رئيسي",
                    hashed_token=hash_secret(settings.demo_device_token),
                    metadata_json={"seeded": True},
                )
            )

        db.commit()


if __name__ == "__main__":
    seed()
