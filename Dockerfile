# Base Image (Lightweight Python)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for some python packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc6-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install Dependencies
RUN pip install --default-timeout=100 --no-cache-dir -r requirements.txt

# Copy the rest of the app code
COPY . .

# Make startup script executable
RUN chmod +x start.sh

# Create directory for SQLite DB if it doesn't exist
RUN mkdir -p /app/data

# Expose the requested port
EXPOSE 5002

# Environment Variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1
ENV PORT=5002

# Run command (Production Server)
# Binding to 0.0.0.0 is required for Docker containers
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5002", "--timeout", "300", "app:app"]
