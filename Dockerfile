# Dockerfile - TranscriberApp Backend Production
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    mailutils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python deps
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY backend/ ./backend/

# Copy frontend dist
COPY frontend/dist /app/frontend/dist

# Create necessary directories
RUN mkdir -p outputs transcripts audios

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "backend.src.runner.web:app", "--host", "0.0.0.0", "--port", "8000"]
