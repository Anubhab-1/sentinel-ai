# config.py
import os
from dataclasses import dataclass, field
from typing import List, Dict

@dataclass
class Config:
    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    if not SECRET_KEY:
        if os.getenv("FLASK_ENV") == "production":
            raise ValueError("No SECRET_KEY set for production configuration")
        SECRET_KEY = "dev-key-change-in-production"

    DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Security Headers & Cookies
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = os.getenv("FLASK_ENV") == "production"
    
    # Security
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT", "5 per minute") 
    API_KEY: str = os.getenv("API_KEY")
    
    # Use field(default_factory=...) for mutable defaults
    ALLOWED_DOMAINS: List[str] = field(default_factory=lambda: os.getenv("ALLOWED_DOMAINS", "").split(",") if os.getenv("ALLOWED_DOMAINS") else [])
    DISALLOWED_IPS: List[str] = field(default_factory=lambda: os.getenv("DISALLOWED_IPS", "127.0.0.1,::1,0.0.0.0").split(","))
    
    # Scanner
    SCAN_TIMEOUT: int = int(os.getenv("SCAN_TIMEOUT", "30"))
    MAX_REDIRECTS: int = int(os.getenv("MAX_REDIRECTS", "5"))
    
    # AI
    # AI
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "").strip()
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", "30"))
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///sentinel.db")
    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL

    # Celery / Redis
    # Render provides REDIS_URL, we map it to Celery if simple config
    _REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", _REDIS_URL)
    CELERY_RESULT_BACKEND: str = os.getenv("CELERY_RESULT_BACKEND", _REDIS_URL)

    
    # Features
    ENABLE_PORT_SCAN: bool = os.getenv("ENABLE_PORT_SCAN", "true").lower() == "true"
    ENABLE_AI: bool = os.getenv("ENABLE_AI", "true").lower() == "true"

    # --- CONSTANTS ---
    SECURITY_HEADERS: List[str] = field(default_factory=lambda: [
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy"
    ])

    COMMON_PORTS: Dict[int, str] = field(default_factory=lambda: {
        21: "FTP",
        22: "SSH",
        23: "Telnet",
        25: "SMTP",
        53: "DNS",
        80: "HTTP",
        443: "HTTPS",
        445: "SMB",
        3306: "MySQL",
        8080: "HTTP-Alt"
    })

    RISK_WEIGHTS: Dict[str, int] = field(default_factory=lambda: {
        "High": 20, 
        "Medium": 10, 
        "Low": 2
    })

config = Config()