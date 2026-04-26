from pydantic import BaseModel

from app.schemas.common import ORMModel


class DeviceRead(ORMModel):
    id: str
    code: str
    name: str
    location_label: str
    is_active: bool
    last_seen_at: str | None = None
    notes: str | None = None
    metadata_json: dict


class DeviceCreate(BaseModel):
    code: str
    name: str
    location_label: str
    notes: str | None = None
    metadata_json: dict = {}


class DeviceUpdate(BaseModel):
    name: str | None = None
    location_label: str | None = None
    notes: str | None = None
    metadata_json: dict | None = None
    is_active: bool | None = None


class DeviceTokenResponse(BaseModel):
    device: DeviceRead
    plain_token: str
