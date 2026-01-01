import pytest
from unittest.mock import patch, MagicMock
from tasks import scan_task, calculate_risk
from app import app
from database import db, Scan
from celery_app import celery

def test_calculate_risk():
    findings = [
        {"severity": "High"},
        {"severity": "Medium"},
        {"severity": "Low"}
    ]
    # Check your config.py weights: High=20, Medium=10, Low=2 -> Total=32
    assert calculate_risk(findings) == 32

    # Cap at 100
    findings_many = [{"severity": "High"}] * 10 
    assert calculate_risk(findings_many) == 100

def test_scan_task(client):
    # Force Eager Mode (No Broker needed)
    celery.conf.update(
        task_always_eager=True,
        task_eager_propagates=True,
        broker_url='memory://',
        result_backend='cache+memory://'
    )
    
    # Mock asyncio.run(scan_website(url))
    with patch('tasks.scan_website') as mock_scan:
        # Return mock findings
        mock_scan.return_value = (
            [
                {"issue": "Test Issue", "header": "Test Header", "severity": "High", "reasons": ["Test"]}
            ], 
            {
                "technologies": ["Python"],
                "reachable": True,
                "https_context": {},
                "header_consensus": {}
            }
        )
        
        # Mock celery task binding 'self'
        mock_self = MagicMock()
        mock_self.request.id = "test-task-id"
        
        # Run logic inside app context to allow DB access
        with app.app_context():
            # Clear DB
            db.session.query(Scan).delete()
            
            # Execute via apply() to handle bind=True automatically
            task_result = scan_task.apply(args=["https://example.com"])
            result = task_result.result
            
            # Verify Return
            assert result['status'] == 'Complete'
            assert result['result']['risk_score'] >= 20
            
            # Verify DB
            scan = Scan.query.filter_by(url="https://example.com").first()
            assert scan is not None
            assert scan.high_count == 1
