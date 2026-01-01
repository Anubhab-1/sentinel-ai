import json
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Scan(db.Model):
    __tablename__ = "scans"
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    risk_score = db.Column(db.Integer)
    high_count = db.Column(db.Integer)
    medium_count = db.Column(db.Integer)
    low_count = db.Column(db.Integer)
    findings_json = db.Column(db.Text)  # Stored as JSON string
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "url": self.url,
            "risk_score": self.risk_score,
            "created_at": self.created_at.isoformat(),
            "findings": json.loads(self.findings_json) if self.findings_json else [],
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def init_db(app):
    with app.app_context():
        db.create_all()
