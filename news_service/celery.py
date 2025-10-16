import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "news_service.settings")

app = Celery("news_service")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
app.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
app.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/0")
app.conf.task_track_started = True
app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.worker_max_tasks_per_child = 100  # Restart worker after processing 100 tasks
app.conf.worker_concurrency = 4  # Number of concurrent worker processes
