#!/bin/bash

# Social Support Application - Complete Startup Script
# This script starts both FastAPI backend and Streamlit frontend

set -e  # Exit on error

PROJECT_DIR="/Users/marghubakhtar/Documents/social_support_agentic_ai"
cd "$PROJECT_DIR"

# Activate virtual environment
source .venv/bin/activate

echo "════════════════════════════════════════════════════════════════"
echo "Social Support Application - Complete Startup"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if FastAPI is already running
echo -e "${BLUE}[INFO]${NC} Checking for FastAPI on port 8000..."
if ! nc -z localhost 8000 2>/dev/null; then
    echo -e "${GREEN}[OK]${NC} FastAPI port 8000 available"
    
    echo ""
    echo -e "${BLUE}[INFO]${NC} Starting FastAPI backend..."
    echo "  Command: python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
    echo ""
    
    # Start FastAPI in background
    python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload &
    FASTAPI_PID=$!
    
    # Wait for FastAPI to start
    echo -e "${YELLOW}[WAIT]${NC} Waiting for FastAPI to initialize..."
    sleep 3
    
    # Check if FastAPI started successfully
    if nc -z localhost 8000 2>/dev/null; then
        echo -e "${GREEN}[OK]${NC} FastAPI backend started successfully (PID: $FASTAPI_PID)"
        echo "  Available at: http://localhost:8000"
        echo "  API Docs at: http://localhost:8000/docs"
    else
        echo -e "${YELLOW}[WARN]${NC} FastAPI may not have started. Check the output above for errors."
    fi
else
    echo -e "${YELLOW}[WARN]${NC} FastAPI already running on port 8000"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
echo -e "${BLUE}[INFO]${NC} Starting Streamlit frontend (Multi-Page App with Role Switcher)..."
echo "  Command: streamlit run streamlit_app/main_app.py --logger.level=info"
echo "  Access: http://localhost:8501"
echo "  Features: Applicant Portal + Admin Dashboard"
echo ""

# Start Streamlit (runs in foreground)
streamlit run streamlit_app/main_app.py --logger.level=info

# Cleanup on exit
trap "kill $FASTAPI_PID 2>/dev/null || true" EXIT
