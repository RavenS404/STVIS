from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "stvis-worker",
    broker=settings.rabbitmq_url,
    backend=None,
)
celery_app.conf.update(
    task_default_queue="celery",
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone=settings.timezone,
)

celery_app.autodiscover_tasks(["worker.app"])
