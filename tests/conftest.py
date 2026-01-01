import os
import sys

import pytest

# Ensure project root is in sys.path so tests can import application modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app as _app  # noqa: F401, E402


from database import db

@pytest.fixture
def client():
    _app.config["TESTING"] = True
    # use in-memory db for speed
    _app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    
    with _app.test_client() as client:
        with _app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()
