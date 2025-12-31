#!/bin/bash

# UAE Social Support System - Streamlit App Launcher
# FAANG-Grade Production Startup Script

echo "🇦🇪 UAE Social Support System"
echo "================================"
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not detected"
    echo "Attempting to activate..."
    
    if [ -f "../.venv/bin/activate" ]; then
        source ../.venv/bin/activate
        echo "✅ Virtual environment activated"
    else
        echo "❌ Virtual environment not found. Please create one with:"
        echo "   python -m venv .venv"
        echo "   source .venv/bin/activate"
        echo "   pip install -r requirements.txt"
        exit 1
    fi
fi

# Check if FastAPI is running
echo ""
echo "🔍 Checking FastAPI backend..."
if curl -s http://localhost:8000/ > /dev/null; then
    echo "✅ FastAPI is running on http://localhost:8000"
else
    echo "⚠️  FastAPI not detected on port 8000"
    echo ""
    echo "Please start the FastAPI server first:"
    echo "  cd .."
    echo "  uvicorn src.api.main:app --reload"
    echo ""
    read -p "Start anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Launch Streamlit
echo ""
echo "🚀 Launching Streamlit Application..."
echo "================================"
echo ""
echo "📍 Access the application at:"
echo "   🌐 http://localhost:8501"
echo ""
echo "👨‍💼 Roles Available:"
echo "   🙋 Applicant Portal - Main user journey"
echo "   👨‍💼 Admin Dashboard - System monitoring"
echo ""
echo "⚡ Features:"
echo "   ✅ Real-time application processing"
echo "   ✅ AI-powered eligibility assessment"
echo "   ✅ Interactive chatbot support"
echo "   ✅ System health monitoring"
echo "   ✅ ML model performance metrics"
echo "   ✅ Audit logs & governance"
echo ""
echo "Press Ctrl+C to stop the server"
echo "================================"
echo ""

# Run streamlit
streamlit run main_app.py --server.port 8501 --server.address localhost
