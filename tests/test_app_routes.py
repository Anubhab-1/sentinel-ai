import pytest
from unittest.mock import patch, MagicMock
from app import app, db, Scan

@pytest.fixture
def client():
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for logic tests
    app.config["TESTING"] = True
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_health_check(client):
    """Test the /health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"
    assert response.json["database"] == "connected"

def test_index_get(client):
    """Test loading the main page."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"RakshaNetra" in response.data

def test_index_post_invalid_url(client):
    """Test scanning an invalid URL."""
    # Logic: app.py validate_url returns False -> 400
    # ensure no CSRF block
    response = client.post("/", json={"url": "not-a-url"}, headers={"X-API-Key": "test"})
    assert response.status_code == 400
    assert b"Invalid URL" in response.data

def test_index_post_valid_url(client):
    """Test starting a scan with a valid URL."""
    # Need to set API KEY
    with app.app_context():
        app.config["API_KEY"] = "test-secret-key"
        
    with patch("tasks.scan_task.delay") as mock_task:
        mock_task.return_value.id = "12345"
        response = client.post("/", json={"url": "https://example.com"}, headers={"X-API-Key": "test-secret-key"})
        assert response.status_code == 202
        assert response.json["task_id"] == "12345"

def test_history_empty(client):
    """Test history page with no scans."""
    with client.session_transaction() as sess:
        sess["my_scans"] = []
    response = client.get("/history")
    assert response.status_code == 200
    assert b"No scans found" in response.data or b"Scans" in response.data

def test_download_pdf_404(client):
    """Test downloading a non-existent scan."""
    response = client.get("/download/99999")
    assert response.status_code == 404

def test_download_pdf_success(client):
    """Test downloading a valid PDF."""
    import json
    # Create dummy scan
    findings = [{"issue": "Test", "severity": "High", "recommendation": "Fix it"}]
    scan = Scan(
        url="https://test.com", 
        risk_score=50, 
        findings_json=json.dumps(findings) # Correct Field
    )
    db.session.add(scan)
    db.session.commit()
    
    response = client.get(f"/download/{scan.id}")
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"

