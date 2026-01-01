import json

from app import app
from database import Scan, db


def test_download_pdf(client):
    # Create a sample scan in DB
    with app.app_context():
        db.session.query(Scan).delete()
        sample_findings = [
            {
                "severity": "High",
                "issue": "SQL Injection",
                "recommendation": "Use prepared statements",
                "reference_url": "https://owasp.org",
            },
            {
                "severity": "Low",
                "issue": "Missing Security Header",
                "recommendation": "Add CSP",
                "reference_url": "https://owasp.org",
            },
        ]
        s = Scan(
            url="https://example.com",
            risk_score=42,
            high_count=1,
            medium_count=0,
            low_count=1,
            findings_json=json.dumps(sample_findings),
        )
        db.session.add(s)
        db.session.commit()
        scan_id = s.id

    resp = client.get(f"/download/{scan_id}")
    assert resp.status_code == 200
    assert resp.headers["Content-Type"] == "application/pdf"
    data = resp.data
    # PDF files start with %PDF
    assert data.startswith(b"%PDF")
    assert len(data) > 200
