@echo off
echo Starting FinSense Development Environment...
echo.

echo Starting Backend on http://localhost:8000
start "FinSense Backend" cmd /k "cd /d %~dp0backend && python run_backend.py"

timeout /t 3 /nobreak >nul

echo Starting Frontend on http://localhost:3000
start "FinSense Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Both services are starting...
echo Backend: http://localhost:8000
echo Frontend: http://localhost:3000
echo.
echo Press any key to close this window...
pause >nul


