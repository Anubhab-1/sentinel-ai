# 🛡️ Sentinel AI - Next-Gen Security Scanner
> **Developed by RakshaNetra™**

**Sentinel AI** is an enterprise-grade automated security auditing platform designed to detect, analyze, and explain web vulnerabilities in real-time. Built with a scalable microservices architecture, it leverages AI to provide context-aware remediation strategies.

[![CI Pipeline](https://github.com/Anubhab-1/sentinel-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/Anubhab-1/sentinel-ai/actions)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Key Features

### 🔍 Advanced Scanning Engine
- **Deep Header Analysis**: Checks for missing or misconfigured security headers (CSP, HSTS, X-Frame-Options, etc.).
- **Active Vulnerability Probing**: Use advanced fuzzing to detect **SQL Injection** and **Reflected XSS** attacks.
- **Port Scanning**: Identifies open ports and services exposing potential attack vectors.
- **Technology Fingerprinting**: Automatically detects server stacks (Nginx, Apache) and frontend frameworks.
- **SSRF Protection**: Built-in validation to prevent unauthorized internal network access.

### 🧠 AI-Powered Analysis
- **Context-Aware Explanations**: Uses LLMs (Perplexity Sonar-Pro) to explain *why* a vulnerability matters.
- **Actionable Remediation**: Provides copy-paste fix instructions tailored to the specific issue.

### 📊 Visual Dashboard
- **Real-Time Analytics**: Track total scans, average risk scores, and vulnerability distribution (High/Medium/Low).
- **Interactive Charts**: Powered by Chart.js to visualize security trends over time.
- **History Management**: Detailed audit logs of every scan performed.

### 🏢 Enterprise Architecture
- **Asynchronous Processing**: Powered by **Celery** & **Redis** for non-blocking scans.
- **PostgreSQL Ready**: Native support for high-performance, persistent databases on cloud platforms (Render/Neon).
- **PDF Reporting**: Generates client-ready, branded PDF reports with executive summaries.

---

## 🛠️ Architecture

The system follows a modern microservices pattern:

- **Frontend**: HTML5/CSS3 (Dark Mode, Responsive) with Vanilla JS polling.
- **Backend API**: Flask (Python 3.11) exposing REST endpoints.
- **Task Queue**: Celery workers handling long-running scans.
- **Message Broker**: Redis for task state management.
- **Database**: SQLAlchemy (SQLite for Dev / PostgreSQL ready for Prod).

---

## ⚡ Quick Start (Docker) - Recommended

Get the entire stack running in under 2 minutes.

### 1. Configure Environment
Create a `.env` file in the root directory:
```bash
SECRET_KEY=your-super-secret-key
API_KEY=your-api-key
PERPLEXITY_API_KEY=your-perplexity-key
DATABASE_URL=sqlite:///sentinel.db
```

### 2. Launch with Docker Compose
```bash
docker-compose up --build
```
Access the dashboard at: `http://localhost:5002`

---

## 🔧 Manual Setup (Dev)

If you prefer running locally without Docker:

1. **Install Dependencies**
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Start Redis** (Required for background tasks).

3. **Start Worker** (Terminal 1)
   ```bash
   celery -A celery_worker.celery worker --loglevel=info -P gevent
   ```

4. **Start App** (Terminal 2)
   ```bash
   python app.py
   ```

---

## 🧪 Testing

Run the automated test suite to verify identifying logic and security inputs.

```bash
pytest -q tests/
```

---

## 🔒 Security

This application enforces:
- **Strict API Authentication** (API Keys required for JSON endpoints).
- **CSRF Protection** (Double-submit cookie validation).
- **Input Sanitization** & **Rate Limiting**.

---

© 2025 Sentinel AI Project. All Rights Reserved.
