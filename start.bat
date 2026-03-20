@echo off
echo SW PM 역량 인증 평가 시스템 시작...

set PYTHON=C:\Users\user\AppData\Local\Python\bin\python.exe
set NODE_PATH=C:\Program Files\nodejs
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8

:: 백엔드 시작
echo [1/2] 백엔드 서버 시작...
start "Backend - PM Solution" cmd /k "cd /d C:\Users\user\pmsolution\backend && %PYTHON% -m uvicorn app.main:app --reload --port 8000"

timeout /t 3 /nobreak >nul

:: 프론트엔드 시작
echo [2/2] 프론트엔드 시작...
start "Frontend - PM Solution" cmd /k "set PATH=%NODE_PATH%;%PATH% && cd /d C:\Users\user\pmsolution\frontend && npm run dev"

timeout /t 4 /nobreak >nul

echo.
echo ========================================
echo  시스템 실행 완료!
echo ========================================
echo  브라우저: http://localhost:5173
echo  API 문서: http://localhost:8000/docs
echo ========================================
echo.

start http://localhost:5173
