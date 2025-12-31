from celery_app import celery
import asyncio
from scanner import scan_website
from context import adjust_severity
from confidence import calculate_confidence
from database import db, Scan, AuditLog
from config import config
import json

from references import get_reference

def calculate_risk(findings):
    score = 0
    weights = config.RISK_WEIGHTS
    for f in findings:
        score += weights.get(f["severity"], 0)
    return min(score, 100)

@celery.task(bind=True)
def scan_task(self, url):
    """
    Background Task to scan the website.
    Updates state as it progresses.
    """
    self.update_state(state='PROGRESS', meta={'status': 'Analysing Headers & Port Scan...'})
    
    # Run Async logic synchronously
    findings, metadata = asyncio.run(scan_website(url))
    
    self.update_state(state='PROGRESS', meta={'status': 'Calculating Risk Scores...'})
    
    # Process findings and add References
    for f in findings:
        f["severity"] = adjust_severity(f, metadata)
        if "recommendation" not in f:
            f["recommendation"] = "Apply OWASP guidelines."
        
        # Add OWASP Reference
        f["reference_url"] = get_reference(f["issue"])

    risk_score = calculate_risk(findings)
    confidence_score, confidence_level = calculate_confidence(metadata)

    summary = {
        "High": sum(1 for f in findings if f["severity"] == "High"),
        "Medium": sum(1 for f in findings if f["severity"] == "Medium"),
        "Low": sum(1 for f in findings if f["severity"] == "Low"),
    }
    
    # Capture technologies
    technologies = metadata.get("technologies", [])

    # Save to DB
    new_scan = Scan(
        url=url,
        risk_score=risk_score,
        high_count=summary["High"],
        medium_count=summary["Medium"],
        low_count=summary["Low"],
        findings_json=json.dumps(findings)
    )
    db.session.add(new_scan)
    
    # Audit Log
    log = AuditLog(action="SCAN_ASYNC", details=f"Scanned {url} via Task {self.request.id}")
    db.session.add(log)
    
    db.session.commit()

    return {
        'status': 'Complete', 
        'result': {
            'url': url,
            'risk_score': risk_score,
            'confidence_score': confidence_score,
            'confidence_level': confidence_level,
            'summary': summary,
            'findings': findings,
            'technologies': technologies,
            'scan_id': new_scan.id
        }
    }
