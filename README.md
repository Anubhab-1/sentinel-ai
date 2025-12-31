# 🛡️ Sentinel AI - Next-Gen Security Scanner
> **Developed by NexusLabs™**

**Sentinel AI** is an enterprise-grade automated security auditing platform designed to detect, analyze, and explain web vulnerabilities in real-time. Built with a scalable microservices architecture, it leverages AI to provide context-aware remediation strategies.

[![CI Pipeline](https://github.com/yourusername/sentinel-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/sentinel-ai/actions)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 🚀 Key Features

### 🔍 Advanced Scanning Engine
- **Deep Header Analysis**: Checks for missing or misconfigured security headers (CSP, HSTS, X-Frame-Options, etc.).
- **Port Scanning**: Identifies open ports and services exposing potential attack vectors.
- **Technology Fingerprinting**: Automatically detects server stacks (Nginx, Apache) and frontend frameworks (React, jQuery, Bootstrap).
- **SSRF Protection**: Built-in validation to prevent unauthorized internal network access.

### 🧠 AI-Powered Analysis
- **Context-Aware Explanations**: Uses LLMs (Perplexity Sonar-Pro) to explain *why* a vulnerability matters in plain English.
- **Actionable Remediation**: Provides copy-paste fix instructions tailored to the specific issue.
- **Smart Fallback**: auto-switches to offline knowledge base if the AI service is unreachable.

### 🏢 Enterprise Architecture
- **Asynchronous Processing**: Powered by **Celery** & **Redis** to handle background scans without blocking the UI.
- **Containerized Deployment**: Fully dockerized (App + Worker + Redis) for one-click setup.
- **Audit Logging**: Tracks all authentication attempts and scan activities for compliance.
- **PDF Reporting**: Generates client-ready, branded PDF reports with executive summaries and OWASP references.

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
