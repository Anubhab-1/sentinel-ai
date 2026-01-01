import sys
import os
import pytest

# Ensure project root is in sys.path so tests can import application modules
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app as _app


@pytest.fixture
def client():
    _app.config['TESTING'] = True
    with _app.test_client() as client:
        yield client
