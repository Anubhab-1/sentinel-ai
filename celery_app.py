from celery import Celery
from config import config

def make_celery():
    celery = Celery(
        "app",
        backend=config.result_backend,
        broker=config.CELERY_BROKER_URL
    )
    celery.conf.update(config.__dict__)
    return celery

celery = make_celery()
