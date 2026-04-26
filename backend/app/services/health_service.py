from __future__ import annotations

import logging
from datetime import UTC, datetime

import requests
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models.monitoring import ServiceHeartbeat
from app.services.object_storage import ObjectStorageService
from app.services.inference_dispatcher import celery_client

def _component(status: str, **details) -> dict:
    return {"status": status, "details": details}


_log = logging.getLogger(__name__)


def _rabbitmq_overview() -> tuple[int, dict]:
    settings = get_settings()
    response = requests.get(
        f"{settings.rabbitmq_management_url}/queues/%2F",
        auth=(settings.rabbitmq_management_username, settings.rabbitmq_management_password),
        timeout=3,
    )
    response.raise_for_status()
    queues = response.json()
    total_depth = sum(int(queue.get("messages", 0)) for queue in queues)
    return total_depth, {"queue_count": len(queues)}


def build_system_health(db: Session) -> dict:
    generated_at = datetime.now(UTC).isoformat()
    components = {"backend": _component("ok")}

    try:
        db.execute(text("SELECT 1"))
        components["database"] = _component("ok")
    except Exception as exc:
        _log.warning("Health check: database unavailable: %s", exc)
        components["database"] = _component("error", error="unavailable")

    try:
        storage = ObjectStorageService()
        storage.ensure_bucket()
        components["object_storage"] = _component("ok", bucket=storage.bucket)
    except Exception as exc:
        _log.warning("Health check: object storage unavailable: %s", exc)
        components["object_storage"] = _component("error", error="unavailable")

    queue_depth = 0
    try:
        queue_depth, rabbitmq_details = _rabbitmq_overview()
        components["rabbitmq"] = _component("ok", queue_depth=queue_depth, **rabbitmq_details)
    except Exception as exc:
        _log.warning("Health check: rabbitmq unavailable: %s", exc)
        components["rabbitmq"] = _component("error", error="unavailable")

    try:
        ping = celery_client.control.inspect(timeout=2).ping() or {}
        components["worker"] = _component("ok" if ping else "warning", ping=ping)
    except Exception as exc:
        _log.warning("Health check: worker unavailable: %s", exc)
        components["worker"] = _component("error", error="unavailable")

    heartbeats = {item.service_name: item for item in db.query(ServiceHeartbeat).all()}
    for service_name in ["celery-worker", "model:violation_detection", "model:plate_detection"]:
        heartbeat = heartbeats.get(service_name)
        if heartbeat:
            components[service_name] = _component(
                heartbeat.status,
                last_seen_at=heartbeat.last_seen_at.isoformat(),
                payload=heartbeat.payload_json,
            )
        else:
            components[service_name] = _component("unknown")

    return {"generated_at": generated_at, "components": components}
