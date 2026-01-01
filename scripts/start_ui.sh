#!/bin/bash
# Startup script for Social Support System
# Starts both FastAPI backend and Streamlit frontend

echo "🚀 Starting UAE Social Support System..."
echo "=========================================="
echo ""

# Check if Ollama is running
echo "🔍 Checking if Ollama is running..."
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  WARNING: Ollama is not running!"
    echo "   Please start Ollama with: ollama serve"
    echo ""
else
    echo "✅ Ollama is running"
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p data/databases
mkdir -p data/uploads
mkdir -p data/synthetic
echo "✅ Directories ready"
echo ""

# Start FastAPI backend
echo "🔧 Starting FastAPI backend on http://localhost:8000..."
cd /Users/marghubakhtar/Documents/social_support_agentic_ai
python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000 &
FASTAPI_PID=$!
echo "✅ FastAPI started (PID: $FASTAPI_PID)"
echo ""

# Wait for FastAPI to be ready
echo "⏳ Waiting for FastAPI to be ready..."
sleep 3

# Test FastAPI
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ FastAPI is responding"
else
    echo "⚠️  FastAPI may not be ready yet"
fi
echo ""

# Start Streamlit frontend
echo "🎨 Starting Streamlit UI on http://localhost:8501..."
streamlit run streamlit_app/app.py --server.port 8501 --server.address 0.0.0.0 &
STREAMLIT_PID=$!
echo "✅ Streamlit started (PID: $STREAMLIT_PID)"
echo ""

echo "=========================================="
echo "🎉 System is ready!"
echo ""
echo "📍 Access points:"
echo "   - Frontend UI:  http://localhost:8501"
echo "   - Backend API:  http://localhost:8000"
echo "   - API Docs:     http://localhost:8000/docs"
echo ""
echo "🛑 To stop both services:"
echo "   kill $FASTAPI_PID $STREAMLIT_PID"
echo ""
echo "📝 Logs will appear below..."
echo "=========================================="
echo ""

# Wait for both processes
wait
