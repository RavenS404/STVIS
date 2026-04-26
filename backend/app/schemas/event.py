from pydantic import BaseModel


class EventAssetRead(BaseModel):
    id: str
    kind: str
    mime_type: str
    url: str
