@echo off
echo =================================================================
echo   STUDENT ACADEMIC ADVISOR - STARTING SERVICES
echo =================================================================

start "Academic Advisor - FastAPI Backend" cmd /k "cd backend && .venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

start "Academic Advisor - Vite Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both backend (http://127.0.0.1:8000) and frontend (http://localhost:5173) are launching!
echo API Documentation is available at http://127.0.0.1:8000/api/docs
echo.
