#!/bin/bash
# start.sh

# Start Celery Worker (Low Memory Mode)
celery -A celery_worker.celery worker --loglevel=info --concurrency=1 &

# Start Gunicorn (Low Memory Mode)
# -w 1 means only 1 worker process (Saves ~100MB RAM)
# --threads 4 allows it to handle concurrent requests via threads instead of processes
gunicorn -w 1 --threads 4 -b 0.0.0.0:$PORT --timeout 300 app:app
