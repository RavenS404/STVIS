from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_model import ModelProfile


def list_model_profiles(db: Session) -> list[ModelProfile]:
    return list(db.scalars(select(ModelProfile).order_by(ModelProfile.display_name.asc())))
