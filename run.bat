@echo off
echo ============================================
echo   Veritas Agent - Starting up
echo ============================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\python.exe" (
    echo Virtual environment not found.
    echo Run: python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt
    pause
    exit /b 1
)

REM Check .env
if not exist ".env" (
    echo .env not found. Copying from .env.example...
    if exist ".env.example" copy .env.example .env
    echo Please edit .env with your API keys.
)

echo Starting server on http://localhost:8000 (or next free port)...
echo Press Ctrl+C to stop
echo.

REM Use python run.py which auto-detects free port and opens browser
venv\Scripts\python.exe run.py