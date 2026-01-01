import os
import sys

import pytest

# Ensure project root is in sys.path so tests can import application modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import os
# Ensure tests use an in-memory database during import-time to avoid file permission issues
os.environ['DATABASE_URL'] = os.environ.get('DATABASE_URL', 'sqlite:///:memory:')
os.environ['FLASK_TESTING'] = 'true'
os.environ['CELERY_BROKER_URL'] = 'memory://'
os.environ['CELERY_RESULT_BACKEND'] = 'cache+memory://'
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

@pytest.fixture(autouse=True)
def mock_redis():
    """Mock Redis globally for all tests."""
    from unittest.mock import MagicMock, patch
    
    store = {}
    class FakeRedis:
        def __init__(self):
            self.store = {}
            
        def setex(self, key, time, value):
            self.store[key] = value.encode('utf-8') if isinstance(value, str) else value
            
        def get(self, key):
            return self.store.get(key)
            
        def delete(self, key):
            if key in self.store:
                del self.store[key]
                
        def from_url(self, url):
            return self

    fake = FakeRedis()
    
    # Patch the redis_client object in both app and auth modules
    # Use patch.object on imported modules to be sure
    import app
    import auth
    
    with patch.object(app, 'redis_client', fake), patch.object(auth, 'redis_client', fake):
        yield fake
