from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.event import EvidenceAsset
from app.services.object_storage import ObjectStorageService


def get_asset_bytes(db: Session, asset_id: str) -> tuple[EvidenceAsset, bytes]:
    asset = db.get(EvidenceAsset, asset_id)
    if asset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
    storage = ObjectStorageService()
    return asset, storage.get_bytes(asset.object_key)
