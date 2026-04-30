from __future__ import annotations

from celery import Celery

from app.settings import settings


celery_app = Celery(
    "crypto_alpha_agent",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_max_tasks_per_child=200,
)


celery_app.conf.beat_schedule = {
    "run-alpha-pipeline-every-15-min": {
        "task": "app.worker.tasks.run_alpha_pipeline",
        "schedule": 15 * 60.0,
    }
}
