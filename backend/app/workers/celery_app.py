from celery import Celery

from app.core.config import settings
from app.workers.daily_job import run_daily_refresh

celery = Celery("fund_predictor", broker=settings.redis_url, backend=settings.redis_url)


@celery.task(name="daily_refresh")
def daily_refresh_task():
    return run_daily_refresh()
