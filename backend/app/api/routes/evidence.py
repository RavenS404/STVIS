from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import DbSession, require_roles
from app.services.evidence_service import get_asset_bytes
from common.constants.enums import UserRole

router = APIRouter()


@router.get("/assets/{asset_id}")
def get_asset(asset_id: str, db: DbSession, _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR))):
    asset, content = get_asset_bytes(db, asset_id)
    return Response(content=content, media_type=asset.mime_type)
