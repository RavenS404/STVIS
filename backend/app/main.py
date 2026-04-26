from __future__ import annotations

import logging
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.object_storage import ObjectStorageService

settings = get_settings()
configure_logging(settings.debug)

app = FastAPI(title=settings.app_name, default_response_class=ORJSONResponse)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def attach_request_id(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-Id"] = request.state.request_id
    return response


@app.on_event("startup")
def on_startup() -> None:
    if not settings.debug and settings.secret_key == "change-me-in-production":
        raise RuntimeError(
            "SECRET_KEY is set to the insecure default. "
            "Set a strong SECRET_KEY in .env before running in production."
        )
    ObjectStorageService().ensure_bucket()


app.include_router(api_router, prefix=settings.api_v1_prefix)
