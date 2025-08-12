# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1

# Set work directory
WORKDIR /app

# Install system dependencies for Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ python3-dev \
    libffi-dev libssl-dev \
    libxml2-dev libxslt1-dev \
    libpq-dev git curl wget \
  && rm -rf /var/lib/apt/lists/*

# Copy requirement files first (better build caching)
COPY requirements.txt requirements.desktop.txt ./

# Upgrade pip & install both sets of requirements
RUN python -m pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt -r requirements.desktop.txt

# Copy the full project
COPY . .

# Create necessary directories
RUN mkdir -p logs data backups temp

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app
USER app

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["python", "src/main.py"]
