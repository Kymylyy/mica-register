FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for PostgreSQL
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from backend directory
COPY backend/ .

# Copy data directory (contains CSV files)
COPY data/ /app/data/
# Import scripts will check data/ directory first, then root for backward compatibility

# Expose port (Railway will set PORT env variable)
EXPOSE 8000

# Run the application
# Railway automatically sets PORT env variable and routes traffic
# We use shell form to access environment variable
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}

