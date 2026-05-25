FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend \
    HOME=/home/appuser \
    YOLO_CONFIG_DIR=/home/appuser/.config/Ultralytics

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends build-essential libgl1 libglib2.0-0 libpq-dev && rm -rf /var/lib/apt/lists/*

COPY worker/requirements.txt /tmp/worker-requirements.txt
RUN pip install --no-cache-dir --default-timeout=1000 -r /tmp/worker-requirements.txt

COPY . /app

RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /home/appuser/.config/Ultralytics \
    && chown -R appuser:appuser /app /home/appuser

USER appuser

CMD ["celery", "-A", "worker.app.celery_app.celery_app", "worker", "--loglevel=INFO"]
