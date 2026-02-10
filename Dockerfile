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

# Copy update orchestration scripts (used by Railway cron service)
COPY scripts/ /app/scripts/

# Copy data directory (contains CSV files)
COPY data/ /app/data/
# Import scripts will check data/ directory first, then root for backward compatibility

# Expose port (Railway will set PORT env variable)
EXPOSE 8000

# Make startup script executable (already copied by COPY backend/ .)
RUN chmod +x /app/start.sh

# Use startup script (runs migrations then starts app)
# Shell form needed for ${PORT} environment variable expansion
# Note: start.sh already in /app/ from COPY backend/ . (line 16)
CMD /app/start.sh
