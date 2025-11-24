#!/bin/bash
# Run script for Opus Clip Cloud

echo "Starting Opus Clip Cloud..."
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "Error: Virtual environment not found!"
    echo "Please run setup_cloud.sh first"
    exit 1
fi

# Check if running in production mode
if [ "$1" == "production" ] || [ "$1" == "prod" ]; then
    echo "Starting in PRODUCTION mode with Gunicorn..."
    echo "Workers: 2, Timeout: 1800 seconds (30 minutes)"
    echo ""
    gunicorn -w 2 -b 0.0.0.0:5000 --timeout 1800 --access-logfile - --error-logfile - app_cloud:app
else
    echo "Starting in DEVELOPMENT mode with Flask..."
    echo "For production use: ./run_cloud.sh production"
    echo ""
    python3 app_cloud.py
fi
