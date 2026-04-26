from pydantic import BaseModel


class SettingRead(BaseModel):
    key: str
    value_json: object
    description: str | None = None
    is_secret: bool = False


class SettingUpdate(BaseModel):
    value_json: object
