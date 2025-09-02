# Dockerfile for Medical AI API
FROM python:3.11-slim

WORKDIR /app

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files
COPY ultra_simple.py .

# Run the ultra-simple app
CMD ["python", "ultra_simple.py"]
