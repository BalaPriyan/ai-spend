#!/usr/bin/env bash
set -e

# AI Spends Tracker & Analyzer - Unified Launcher Script
echo "========================================================"
echo "Starting AI Spends Tracker & Analyzer"
echo "========================================================"

if ! command -v uv &> /dev/null; then
    echo "Error: 'uv' is not installed. Please install uv first."
    exit 1
fi

MODE="${1:-frontend}"

if [ "$MODE" == "--backend" ] || [ "$MODE" == "backend" ]; then
    ./backend/run_backend.sh
elif [ "$MODE" == "--all" ] || [ "$MODE" == "all" ]; then
    echo "Launching FastAPI Backend in background on http://localhost:8000 ..."
    uv run uvicorn backend.api:app --host 0.0.0.0 --port 8000 &
    BACKEND_PID=$!
    echo "Launching Streamlit Frontend on http://localhost:8501 ..."
    uv run streamlit run frontend/app.py --server.port 8501 --server.headless true
    kill $BACKEND_PID 2>/dev/null || true
else
    # Default: Frontend
    ./frontend/run_frontend.sh
fi
