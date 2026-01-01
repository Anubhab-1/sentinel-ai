
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from app import app, db, ScheduledScan

@pytest.fixture
def client():
    app.config["WTF_CSRF_ENABLED"] = False
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_scheduled_scan_model():
    """Test next_run calculation."""
    s = ScheduledScan(url="https://test.com", interval_minutes=60, enabled=True)
    # Mock created_at
    s.created_at = datetime(2023, 1, 1, 12, 0, 0)
    
    # First run should be created_at if last_run is None
    assert s.next_run() == s.created_at
    
    # If disabled
    s.enabled = False
    assert s.next_run() is None
    
    # If run previously
    s.enabled = True
    s.last_run = datetime(2023, 1, 1, 13, 0, 0)
    expected = datetime(2023, 1, 1, 14, 0, 0)
    assert s.next_run() == expected

def test_schedules_api(client):
    """Test CRUD for schedules."""
    # Create
    with app.app_context():
        app.config["API_KEY"] = "secret"
    
    headers = {"X-API-Key": "secret"}
    resp = client.post("/schedules", json={"url": "https://foo.com", "interval_minutes": 30}, headers=headers)
    assert resp.status_code == 201
    data = resp.json
    assert data["url"] == "https://foo.com"
    id = data["id"]
    
    # List
    resp = client.get("/schedules", headers=headers)
    assert resp.status_code == 200
    assert len(resp.json["schedules"]) == 1
    
    # Update
    resp = client.put(f"/schedules/{id}", json={"enabled": False}, headers=headers)
    assert resp.status_code == 200
    assert resp.json["enabled"] is False
    
    # Delete
    resp = client.delete(f"/schedules/{id}", headers=headers)
    assert resp.status_code == 200
    
    # Verify gone
    resp = client.get("/schedules", headers=headers)
    assert len(resp.json["schedules"]) == 0

def test_run_scheduled_scans(client):
    """Test the celery task logic."""
    from tasks import run_scheduled_scans
    
    # Create a due scan
    with app.app_context():
        due = ScheduledScan(url="https://due.com", interval_minutes=10)
        due.last_run = datetime.utcnow() - timedelta(minutes=20) # Overdue
        db.session.add(due)
        
        not_due = ScheduledScan(url="https://wait.com", interval_minutes=10)
        not_due.last_run = datetime.utcnow() # Just ran
        db.session.add(not_due)
        db.session.commit()
        
        with patch("tasks.scan_task.delay") as mock_delay:
            res = run_scheduled_scans.apply(args=()).result
            
            assert due.id in res["triggered"]
            assert not_due.id not in res["triggered"]
            mock_delay.assert_called_with("https://due.com")
