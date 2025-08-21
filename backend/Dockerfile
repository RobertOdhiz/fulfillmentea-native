# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libffi-dev \
        libssl-dev \
        libjpeg-dev \
        libpng-dev \
        libgif-dev \
        libwebp-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libxcb1-dev \
        libxrandr-dev \
        libxss-dev \
        libasound2-dev \
        libpango1.0-dev \
        libcairo2-dev \
        libgdk-pixbuf2.0-dev \
        libgtk-3-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
        libjpeg-dev \
        libpng-dev \
        libtiff-dev \
        libjasper-dev \
        libwebp-dev \
        libgif-dev \
        libopenjp2-7-dev \
        libtiff5-dev \
        libfreetype6-dev \
        liblcms2-dev \
        libharfbuzz-dev \
        libfribidi-dev \
        libxcb1-dev \
        libxrandr-dev \
        libxss-dev \
        libasound2-dev \
        libpango1.0-dev \
        libcairo2-dev \
        libgdk-pixbuf2.0-dev \
        libgtk-3-dev \
        libavcodec-dev \
        libavformat-dev \
        libswscale-dev \
        libv4l-dev \
        libxvidcore-dev \
        libx264-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create media directory
RUN mkdir -p backend/media

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser \
    && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
