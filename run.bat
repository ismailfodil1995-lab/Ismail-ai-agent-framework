@echo off
TITLE Ismail Smart Agent V2.1 Launcher
echo ===================================================
echo   Starting Ismail Smart Agent API Server...
echo ===================================================

IF NOT EXIST ".env" (
    echo [INFO] Creating .env from .env.example...
    copy .env.example .env
)

echo [INFO] Checking Python environment...
python -m pip install -r requirements.txt --quiet

echo [INFO] Starting FastAPI Server on http://localhost:8000 ...
echo [INFO] Swagger Docs available at: http://localhost:8000/docs
uvicorn api_server:app --host 0.0.0.0 --port 8000 --reload
pause
