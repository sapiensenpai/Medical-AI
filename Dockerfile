# Dockerfile for Medical AI API
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY *.py ./
COPY medications.jsonl ./

# Create necessary directories
RUN mkdir -p logs audit trained_models

# Set environment variables
ENV FLASK_APP=flask_medical_api.py
ENV FLASK_ENV=production
ENV PYTHONPATH=/app

# Expose port (Railway uses dynamic PORT)
EXPOSE $PORT

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Run the Railway-optimized application
CMD ["python", "railway_app.py"]
