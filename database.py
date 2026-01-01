import json
from datetime import datetime, timedelta

from flask_sqlalchemy import SQLAlchemy

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Scan(db.Model):
    __tablename__ = "scans"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Linked to User
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
            "high": self.high_count,
            "medium": self.medium_count,
            "low": self.low_count,
            "findings": json.loads(self.findings_json) if self.findings_json else [],
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    details = db.Column(db.String(500))
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ScheduledScan(db.Model):
    """Simple interval-based schedule for recurring scans.

    Fields:
      - url: target to scan
      - interval_minutes: how often to run (integer minutes)
      - enabled: toggle
      - last_run: last run timestamp
    """

    __tablename__ = "scheduled_scans"
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    interval_minutes = db.Column(db.Integer, default=60, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def next_run(self):
        """Return the next run datetime or None if disabled."""
        if not self.enabled:
            return None
        if not self.last_run:
            return self.created_at
        return self.last_run + timedelta(minutes=self.interval_minutes)


def init_db(app):
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            # Race condition safe: If multiple workers start, they might clash on table creation.
            # Postgres logs this as "UniqueViolation" for types. We can safely ignore it.
            print(f"⚠️  Database Schema Creation / Check Warning: {e}")
            pass
