# config.py
import os
from datetime import timedelta
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class Config:
    # Flask
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-key-change-in-production")
    if (
        SECRET_KEY == "dev-key-change-in-production"
        and os.getenv("FLASK_ENV") == "production"
    ):
        raise ValueError("No SECRET_KEY set for production configuration")

    DEBUG: bool = os.getenv("FLASK_DEBUG", "false").lower() == "true"

    # Security Headers & Cookies
    SESSION_COOKIE_HTTPONLY: bool = True
    SESSION_COOKIE_SAMESITE: str = "Lax"
    SESSION_COOKIE_SECURE: bool = os.getenv("FLASK_ENV") == "production"
    
    # Session & CSRF Settings
    # Fix: "CSRF token expired" issues by extending lifetime
    WTF_CSRF_TIME_LIMIT: int = None  # None = valid for session life
    PERMANENT_SESSION_LIFETIME: timedelta = timedelta(days=7)  # Keep logged in for 7 days

    # Security
    RATE_LIMIT_PER_MINUTE: str = os.getenv("RATE_LIMIT", "60 per minute")
    API_KEY: str = os.getenv("API_KEY", "")

    # Use field(default_factory=...) for mutable defaults
    ALLOWED_DOMAINS: List[str] = field(
        default_factory=lambda: (
            os.getenv("ALLOWED_DOMAINS", "").split(",")
            if os.getenv("ALLOWED_DOMAINS")
            else []
        )
    )
    DISALLOWED_IPS: List[str] = field(
        default_factory=lambda: os.getenv(
            "DISALLOWED_IPS", "127.0.0.1,::1,0.0.0.0"
        ).split(",")
    )

    # Scanner
    SCAN_TIMEOUT: int = int(os.getenv("SCAN_TIMEOUT", "30"))
    MAX_REDIRECTS: int = int(os.getenv("MAX_REDIRECTS", "5"))

    # AI
    # AI
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "").strip()
    AI_TIMEOUT: int = int(os.getenv("AI_TIMEOUT", "30"))

    # Database
    # Use absolute path in Docker to ensure persistence in volume
    _env_db_url = os.getenv("DATABASE_URL", "")
    
    # 1. Debug Print (Safe version)
    _safe_print_url = _env_db_url if not _env_db_url else f"{_env_db_url[:15]}..."
    print(f"🔧 DEBUG: Loading DATABASE_URL from Env: '{_safe_print_url}'")

    # 2. Heuristic Check: If it looks garbage, ignore it
    if not _env_db_url or len(_env_db_url.strip()) < 10:
        print("⚠️  Invalid or empty DATABASE_URL detected. Falling back to internal SQLite.")
        _env_db_url = "sqlite:////app/sentinel.db"
    
    # Clean up quotes and fix postgres protocol
    DATABASE_URL: str = _env_db_url.strip().strip('"').strip("'")
    
    # 3. Protocol Enforcement
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
        
    # 4. Final Safety Check
    if not DATABASE_URL.startswith(("sqlite:", "postgresql:", "mysql:")):
         print(f"⚠️  Unknown protocol in '{DATABASE_URL}'. Falling back to internal SQLite.")
         DATABASE_URL = "sqlite:////app/sentinel.db"

         DATABASE_URL = "sqlite:////app/sentinel.db"

    SQLALCHEMY_DATABASE_URI: str = DATABASE_URL
    
    # Fix for "SSL connection has been closed unexpectedly" (common in Cloud DBs)
    # pool_pre_ping: Checks connection liveliness before use
    # pool_recycle: Refreshes connections every 5 mins to avoid timeout
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
        "pool_size": 5,      # Keep 5 connections open
        "max_overflow": 10   # Allow up to 10 more if needed
    }

    # Celery / Redis
    # Render provides REDIS_URL, we map it to Celery if simple config
    _REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    CELERY_BROKER_URL: str = os.getenv("CELERY_BROKER_URL", _REDIS_URL)
    result_backend: str = os.getenv("CELERY_RESULT_BACKEND", _REDIS_URL)

    # Features
    ENABLE_PORT_SCAN: bool = os.getenv("ENABLE_PORT_SCAN", "true").lower() == "true"
    ENABLE_AI: bool = os.getenv("ENABLE_AI", "true").lower() == "true"
    
    # Mail Config (For OTP)
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS: bool = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER: str = os.getenv("MAIL_DEFAULT_SENDER", MAIL_USERNAME)
    MAIL_DEBUG: bool = True  # Force debug logging for mail

    # --- CONSTANTS ---
    SECURITY_HEADERS: List[str] = field(
        default_factory=lambda: [
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "X-Frame-Options",
            "X-Content-Type-Options",
            "Referrer-Policy",
        ]
    )

    COMMON_PORTS: Dict[int, str] = field(
        default_factory=lambda: {
            21: "FTP",
            22: "SSH",
            23: "Telnet",
            25: "SMTP",
            53: "DNS",
            80: "HTTP",
            443: "HTTPS",
            445: "SMB",
            3306: "MySQL",
            8080: "HTTP-Alt",
        }
    )

    RISK_WEIGHTS: Dict[str, int] = field(
        default_factory=lambda: {"High": 20, "Medium": 10, "Low": 2}
    )


config = Config()
