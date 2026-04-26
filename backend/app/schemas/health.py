from pydantic import BaseModel


class ComponentHealth(BaseModel):
    status: str
    details: dict = {}


class SystemHealthResponse(BaseModel):
    generated_at: str
    components: dict[str, ComponentHealth]
