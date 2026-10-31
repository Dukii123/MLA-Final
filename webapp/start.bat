@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\bin\python" (
  echo Phat hien .venv tao tren macOS. Xoa thu muc .venv roi chay lai.
  pause
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Chua co moi truong .venv. Chay lan dau:
  echo   py -3.12 -m venv .venv
  echo   .venv\Scripts\python -m pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

if "%PORT%"=="" set "PORT=8000"
echo MLA Nhom 05 - mo http://127.0.0.1:%PORT%
echo Lan dau nap wav2vec co the mat 30-60 giay. Ctrl+C de dung.
".venv\Scripts\python.exe" -m uvicorn app:app --host 127.0.0.1 --port %PORT%
pause
