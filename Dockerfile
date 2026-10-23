# Use lightweight official Python image
FROM python:3.11-slim

# Install system dependencies: ffmpeg for media remuxing, curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Set environment defaults
ENV PYTHONUNBUFFERED=1
ENV PORT=5000

# Expose Render application port
EXPOSE 5000

# Start high-performance Gunicorn with multi-threaded workers for concurrent streams
CMD ["sh", "-c", "gunicorn -w 2 -k gthread --threads 4 --timeout 120 -b 0.0.0.0:${PORT:-5000} app:app"]
