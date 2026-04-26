from celery import Celery

from app.core.config import get_settings

settings = get_settings()
celery_client = Celery("stvis-backend-dispatcher", broker=settings.rabbitmq_url)


def enqueue_event_processing(event_id: str, inference_run_id: str) -> str:
    task = celery_client.send_task(
        "worker.process_event",
        kwargs={"event_id": event_id, "inference_run_id": inference_run_id},
    )
    return task.id
