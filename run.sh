#!/usr/bin/env bash
set -e

echo "==================================================="
echo "  Starting Ismail Smart Agent API Server..."
echo "==================================================="

if [ ! -f ".env" ]; then
    echo "[INFO] Creating .env from .env.example..."
    cp .env.example .env
fi

echo "[INFO] Installing requirements..."
pip install -r requirements.txt --quiet

echo "[INFO] Starting FastAPI Server on http://localhost:8000 ..."
echo "[INFO] Swagger Docs available at: http://localhost:8000/docs"
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
