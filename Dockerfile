FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    curl \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements-cpu.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Install the package in development mode
RUN pip install -e .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV VECTOR_DB_PATH=/app/data

# Create data directories with proper permissions
RUN mkdir -p /app/data && \
    chmod -R 777 /app/data

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application
CMD ["python", "examples/lightrag_openai_compatible_demo_rabbitmq.py"]
