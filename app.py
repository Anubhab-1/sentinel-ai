import json
from flask import Flask, render_template, request, jsonify, session
from config import config
from scanner import scan_website
from context import adjust_severity
from confidence import calculate_confidence
from ai_explainer import explain_finding
from database import init_db
from fpdf import FPDF
from flask import make_response


from flask_wtf.csrf import CSRFProtect, generate_csrf
from database import db, init_db, Scan, AuditLog
from flasgger import Swagger

from celery_app import celery

from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
# Tell Flask it is behind a Proxy (Render Load Balancer)
# This fixes Rate Limiting and HTTP/HTTPS links
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
app.config.from_object(config)

# FORCE LOAD: Ensure Celery Broker is set (Render Fix)
import os
if not app.config.get('CELERY_BROKER_URL'):
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    app.config['CELERY_BROKER_URL'] = redis_url
    app.config['CELERY_RESULT_BACKEND'] = redis_url
    print(f"🔧 Manual Config Override: Broker set to {redis_url}")
else:
    print(f"✅ Config Loaded: Broker is {app.config['CELERY_BROKER_URL']}")
db.init_app(app)
csrf = CSRFProtect(app)
swagger = Swagger(app)

# Initialize Celery
# Celery is initialized in celery_app.py

from tasks import scan_task # Import after celery initialization

init_db(app)


import re


# -----------------------------
# Risk score calculation
# -----------------------------
def calculate_risk(findings):
    score = 0
    weights = config.RISK_WEIGHTS
    for f in findings:
        score += weights.get(f["severity"], 0)
    return min(score, 100)

def validate_url(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    return re.match(regex, url) is not None

import logging
import functools
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from security import is_safe_url, sanitize_input
from logging_config import setup_logging
from prometheus_flask_exporter import PrometheusMetrics

# -----------------------------
# Configuration & Setup
# -----------------------------

# Configure Logging (Structured JSON)
logger = setup_logging()

# Initialize Prometheus Metrics
metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

# Initialize Limiter
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[config.RATE_LIMIT_PER_MINUTE],
    storage_uri="memory://"
)

# Authentication Decorator
def require_api_key(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        # 1. API Key Check (Strict for API Clients)
        api_key = request.headers.get("X-API-Key")
        if api_key and api_key == config.API_KEY:
             return f(*args, **kwargs)
        
        # 2. Browser Session Check (UI fallback)
        # If it's a browser request coming from our UI, it will have a CSRF token valid 
        # (checked by Flask-WTF globally or specifically if we enable it per route).
        # We assume if the request is NOT JSON/API-intended, it's the browser.
        # But for strict security:
        if request.headers.get("X-CSRFToken") or "csrf_token" in request.form:
             # Flask-WTF handles the validation. If we are here, it passed or is exempt.
             # We rely on Flask-WTF's protections for UI users.
             pass
        elif request.is_json and not api_key: 
             # JSON request without key -> Reject
             log_audit_event("AUTH_FAILURE", f"Invalid credentials from {request.remote_addr}")
             return jsonify({"error": "Unauthorized: Missing or Invalid API Key"}), 401
             
        return f(*args, **kwargs)
    return decorated_function

def log_audit_event(action, details):
    try:
        log = AuditLog(action=action, details=details, ip_address=request.remote_addr)
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        logger.error(f"Audit Log Error: {e}")

# -----------------------------
# Health Check
# -----------------------------
@app.route("/health")
def health():
    try:

        # Check DB connection using SQLAlchemy
        db.session.execute(db.text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        logger.error(f"Health Check DB Error: {e}")
        db_status = "error"
        return jsonify({"status": "error", "database": "disconnected"}), 500

    return jsonify({"status": "ok", "database": db_status})

@app.errorhandler(404)
def not_found_error(error):
    if request.is_json:
        return jsonify({"error": "Resource not found"}), 404
    return render_template('error.html', error_code=404, error_message="We couldn't find the page you're looking for."), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server Error: {error}")
    if request.is_json:
        return jsonify({"error": "Internal Server Error"}), 500
    return render_template('error.html', error_code=500, error_message="Something went wrong on our end."), 500

import asyncio

# -----------------------------
# Main scan route
# -----------------------------
@app.route("/", methods=["GET", "POST"])
@limiter.limit(config.RATE_LIMIT_PER_MINUTE)
@require_api_key
def index():
    """
    Core Scanner Endpoint
    ---
    tags:
      - Scanner
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            url:
              type: string
              example: "https://example.com"
    responses:
      202:
        description: Scan started successfully
        schema:
          properties:
            task_id:
              type: string
    """
    if request.method == "POST":
        # Handle JSON (AJAX) or Form data
        data = request.get_json() if request.is_json else request.form
        url = data.get("url")

        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        url = sanitize_input(url)

        if not validate_url(url):
             return jsonify({"error": "Invalid URL format. Must include http:// or https://"}), 400

        # SSRF Check
        if not is_safe_url(url):
             logger.warning(f"SSRF Attempt detected for URL: {url} from IP: {request.remote_addr}")
             return jsonify({"error": "Security Alert: Target is a forbidden internal address."}), 403

        # Trigger Background Task
        task = scan_task.delay(url)
        
        return jsonify({"task_id": task.id}), 202

    return render_template("index.html", report=None)

@app.route("/status/<task_id>")
def task_status(task_id):
    task = scan_task.AsyncResult(task_id)
    if task.state == 'PENDING':
        response = {
            'state': task.state,
            'status': 'Pending...'
        }
    elif task.state != 'FAILURE':
        response = {
            'state': task.state,
            'status': task.info.get('status', '') if task.info else '',
            'result': task.info.get('result', {}) if task.state == 'SUCCESS' else None
        }
        # PRIVACY FEATURE:
        # If successfully finished, save this Scan ID to the user's session cookie
        if task.state == 'SUCCESS':
            result = task.info.get('result', {})
            scan_id = result.get('scan_id')
            if scan_id:
                my_scans = session.get('my_scans', [])
                if scan_id not in my_scans:
                    my_scans.append(scan_id)
                    session['my_scans'] = my_scans
                    session.modified = True
    else:
        # something went wrong in the background job
        response = {
            'state': task.state,
            'status': str(task.info),  # this is the exception raised
        }
    return jsonify(response)

# -----------------------------
# History page
# -----------------------------
@app.route("/history")
def history():
    # PRIVACY FEATURE: Only show scans belonging to this browser session
    my_ids = session.get('my_scans', [])
    
    if not my_ids:
        scans = []
    else:
        # Filter: ID must be in my_ids list
        scans = Scan.query.filter(Scan.id.in_(my_ids)).order_by(Scan.created_at.desc()).all()
    
    # Convert ORM objects to dicts for template
    scans_data = [s.to_dict() for s in scans]
    
    # Prepare data for Chart.js (Take last 10, reverse for chronological order)
    chart_data = scans_data[:10][::-1]
    
    # Create clean lists
    labels = [s['created_at'][:10] for s in chart_data]
    scores = [s['risk_score'] for s in chart_data]
    
    return render_template("history.html", 
                           scans=scans, 
                           labels=json.dumps(labels),  # Pass as JSON strings
                           scores=json.dumps(scores))

# -----------------------------
# AI Explanation
# -----------------------------
@app.route("/explain", methods=["POST"])
@csrf.exempt
@limiter.limit("10 per minute") # Protect Perplexity API cost
def explain():
    data = request.json
    try:
        explanation = explain_finding(
            data.get("issue"),
            data.get("severity"),
            data.get("reasons", [])
        )
    except Exception as e:
        logger.error(f"Explanation Error: {e}")
        explanation = "AI service unavailable. Please check OWASP for manual guidance."
        
    return jsonify({"explanation": explanation})


# -----------------------------
# Compare last two scans (Missing Part)
# -----------------------------

@app.route("/compare/<path:url>")
def compare(url):
    # Get the last 2 scans for this specific URL
    scans = Scan.query.filter_by(url=url).order_by(Scan.created_at.desc()).limit(2).all()

    if len(scans) < 2:
        return "Need at least 2 scans of this URL to compare."

    latest = scans[0].to_dict()
    previous = scans[1].to_dict()

    # Calculate score difference
    diff = latest["risk_score"] - previous["risk_score"]

    return render_template(
        "compare.html",
        url=url,
        latest=latest,
        previous=previous,
        diff=diff
    )


class PDFReport(FPDF):
    def header(self):
        # Background Header
        self.set_fill_color(10, 25, 47) # Dark Navy (Matches UI)
        self.rect(0, 0, 210, 40, 'F')
        
        # Logo
        try:
            self.image('static/logo.jpg', 10, 5, 30) # X, Y, W
            self.set_xy(45, 10) # Move text cursor to right of logo
        except:
            self.set_xy(10, 10) # Fallback if logo missing

        # Title "SENTINEL AI"
        self.set_font('Arial', 'B', 24)
        self.set_text_color(100, 255, 218) # Cyan Accent
        self.cell(0, 15, 'SENTINEL AI', 0, 1, 'L', fill=False)
        
        # Subtitle
        self.set_font('Arial', '', 10)
        self.set_text_color(200, 200, 200)
        self.cell(0, 5, 'Advanced Security Scanner & Audit Tool | RakshaNetra(TM)', 0, 1, 'L', fill=False)
        
        self.ln(15)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(128)
        self.cell(0, 10, f'Page {self.page_no()} | RakshaNetra(TM) Security', 0, 0, 'C')

def clean_pdf_text(text):
    """Sanitize text for FPDF (Strict ASCII only)"""
    try:
        # Normalize to closest ASCII equivalent, strip everything else
        return str(text).encode('ascii', 'ignore').decode('ascii')
    except:
        return ""

import sys

@app.route("/download/<int:scan_id>")
def download_pdf(scan_id):
    # Increase recursion depth just for this complex PDF generation
    sys.setrecursionlimit(2000)
    
    try:
        scan = Scan.query.get(scan_id)

        if not scan:
            return "Scan not found", 404
        
        scan_dict = scan.to_dict()
        findings = scan_dict['findings']

        # Initialize Custom PDF
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=25)
        pdf.add_page()
        
        # --- Executive Summary Section ---
        pdf.set_xy(10, 45)
        
        # Target Info
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(20, 10, "Target:", 0, 0)
        pdf.set_font("Arial", "", 12)
        
        # Use MultiCell for URL to prevent page break loops on long strings
        pdf.multi_cell(0, 10, clean_pdf_text(scan_dict['url']))
        
        pdf.set_font("Arial", "B", 12)
        pdf.cell(20, 10, "Date:", 0, 0)
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, str(scan_dict['created_at']), 0, 1)
        
        pdf.ln(5)

        # Score Card
        pdf.set_fill_color(240, 248, 255) # AliceBlue
        pdf.set_draw_color(200, 200, 200)
        pdf.rect(10, pdf.get_y(), 190, 25, 'DF')
        
        pdf.set_xy(15, pdf.get_y() + 7)
        pdf.set_font("Arial", "B", 16)
        pdf.set_text_color(10, 25, 47)
        pdf.cell(50, 10, f"Risk Score: {scan_dict['risk_score']}/100", 0, 0)
        
        # Determine Status
        score = scan_dict['risk_score']
        status = "SECURE" if score < 30 else "VULNERABLE" if score > 70 else "AT RISK"
        color = (22, 163, 74) if score < 30 else (220, 38, 38) if score > 70 else (217, 119, 6)
        
        pdf.set_text_color(*color)
        pdf.cell(0, 10, f"Status: {status}", 0, 1, 'R')
        pdf.ln(15)

        # --- Detailed Findings Header ---
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(0, 10, "Detailed Security Findings", 0, 1)
        pdf.set_draw_color(100, 255, 218) # Cyan Line
        pdf.set_line_width(1)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        # --- Findings Table ---
        for f in findings:
            # MANUAL PAGE BREAK CHECK
            # If we are close to bottom (A4 height is 297mm), add page
            # This prevents infinite loops and layout corruption
            if pdf.get_y() > 250:
                pdf.add_page()
                pdf.set_xy(10, 45) # Reset to below header

            # Card Background
            pdf.set_fill_color(255, 255, 255)
            pdf.set_draw_color(230, 230, 230)
            pdf.set_line_width(0.2)
            
            start_y = pdf.get_y()
            
            # Severity Badge
            severity = f['severity'].upper()
            if severity == "HIGH":
                pdf.set_fill_color(254, 226, 226) # Light Red
                pdf.set_text_color(220, 38, 38)
            elif severity == "MEDIUM":
                pdf.set_fill_color(254, 243, 199) # Light Orange
                pdf.set_text_color(217, 119, 6)
            else:
                pdf.set_fill_color(220, 252, 231) # Light Green
                pdf.set_text_color(22, 163, 74)

            pdf.set_font("Arial", "B", 10)
            # Draw badge rect
            pdf.rect(10, start_y, 25, 8, 'F')
            pdf.set_xy(10, start_y)
            pdf.cell(25, 8, severity, 0, 0, 'C')
            
            # Issue Title
            pdf.set_xy(40, start_y)
            pdf.set_font("Arial", "B", 11)
            pdf.set_text_color(10, 25, 47)
            pdf.cell(0, 8, clean_pdf_text(f['issue']), 0, 1)
            
            # Divider
            pdf.ln(2)
            
            # Recommendation
            pdf.set_font("Arial", "", 10)
            pdf.set_text_color(60, 60, 60)
            rec_text = f"Fix: {f.get('recommendation', 'Check OWASP guidelines')}"
            pdf.multi_cell(0, 6, clean_pdf_text(rec_text))
            
            # Reference Link
            if f.get('reference_url'):
                pdf.set_font("Arial", "U", 9)
                pdf.set_text_color(0, 102, 204) # Link Blue
                pdf.cell(0, 6, "OWASP Reference", link=f['reference_url'], ln=1)
            
            pdf.ln(4)
            pdf.set_draw_color(240, 240, 240)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y()) # Separator
            pdf.ln(4)

        # Output
        # STANDARD FPDF OUTPUT (No double encoding)
        pdf_content = pdf.output(dest='S').encode('latin-1')

        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=sentinel_report_{scan_id}.pdf'
        return response

    except Exception as e:
        logger.error(f"PDF Gen Critical Error: {e}")
        return jsonify({"error": f"PDF Generation Failed: {str(e)}"}), 500
if __name__ == "__main__":
    app.run(debug=True, port=5002)