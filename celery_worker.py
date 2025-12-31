from app import app
from celery_app import celery

# Push app context so tasks can use the DB
app.app_context().push()

if __name__ == "__main__":
    celery.start()
