from pydantic import BaseModel

from common.constants.enums import ModelKey


class ModelProfileRead(BaseModel):
    id: str
    model_key: ModelKey
    display_name: str
    artifact_path: str
    version: str
    class_map: dict
    metadata_json: dict
    is_active: bool
