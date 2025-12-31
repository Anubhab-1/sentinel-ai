#!/bin/bash
# start.sh

# Start Celery Worker in the background
# We use & to put it in the background
celery -A celery_worker.celery worker --loglevel=info &

# Start Gunicorn (Web Server) in the foreground
# $PORT is provided by Render
gunicorn -w 4 -b 0.0.0.0:$PORT --timeout 300 app:app
