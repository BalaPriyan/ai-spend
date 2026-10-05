#!/usr/bin/env bash
set -e

# Run FastAPI backend server on port 8000
echo "Starting AI Spends Tracker FastAPI Backend on http://localhost:8000 ..."
echo "Interactive Swagger Docs available at http://localhost:8000/docs"
uv run uvicorn backend.api:app --host 0.0.0.0 --port 8000 --reload
