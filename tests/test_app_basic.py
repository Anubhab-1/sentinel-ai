import pytest
from app import validate_url, app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_validate_url_valid():
    assert validate_url("https://example.com")


def test_validate_url_invalid():
    assert not validate_url("not-a-url")


def test_index_get(client):
    resp = client.get('/')
    assert resp.status_code == 200


def test_health(client):
    resp = client.get('/health')
    assert resp.status_code in (200, 500)
    data = resp.get_json()
    assert data is not None and 'status' in data
