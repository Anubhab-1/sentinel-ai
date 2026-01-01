from celery import Celery

from config import config


def make_celery():
    celery = Celery(
        "app", backend=config.result_backend, broker=config.CELERY_BROKER_URL
    )
    celery.conf.update(config.__dict__)

    # Simple periodic schedule to run scheduled scans every minute.
    # This uses Celery beat if enabled in deployment.
    celery.conf.beat_schedule = getattr(celery.conf, "beat_schedule", {})
    celery.conf.beat_schedule.update(
        {
            "run-scheduled-scans": {
                "task": "tasks.run_scheduled_scans",
                "schedule": 60.0,
            }
        }
    )

    return celery


celery = make_celery()
