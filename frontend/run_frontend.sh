#!/usr/bin/env bash
set -e

# Run Streamlit frontend dashboard on port 8501
echo "Starting AI Spends Tracker Streamlit Frontend on http://localhost:8501 ..."
uv run streamlit run frontend/app.py --server.port 8501 --server.headless true
