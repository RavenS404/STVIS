from pydantic import BaseModel


class IngestEventResponse(BaseModel):
    event_id: str
    case_count_hint: int = 0
    status: str
