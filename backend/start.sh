#!/bin/bash
set -euo pipefail  # Exit on error, undefined vars, pipe failures

echo "=========================================="
echo "MiCA Register - Production Startup"
echo "=========================================="
echo ""

# Run database migrations
echo "[*] Running database migrations..."
echo ""

echo "Running migration 001: Performance indexes..."
python migrations/001_add_performance_indexes.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Migration 001 failed!"
    exit 1
fi
echo ""

echo "Running migration 002: Multi-register schema..."
python migrations/002_multi_register_migration.py
if [ $? -ne 0 ]; then
    echo "[ERROR] Migration 002 failed!"
    exit 1
fi
echo ""

echo "[OK] All migrations completed successfully"
echo ""

# Start FastAPI application
echo "=========================================="
echo "[*] Starting FastAPI application..."
echo "=========================================="
echo ""
echo "Listening on 0.0.0.0:${PORT:-8000}"
echo ""

# Use exec to replace shell with uvicorn (proper signal handling)
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
