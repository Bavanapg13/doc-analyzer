from celery import Celery

from .config import get_settings

settings = get_settings()

celery_app = Celery(
    "document_analyzer",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.tasks"],
)

celery_app.conf.update(
    task_always_eager=settings.celery_task_always_eager,
    task_store_eager_result=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
)
