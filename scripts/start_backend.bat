@echo off
echo Starting CryptoQuant AI Backend...
cd /d %~dp0..
pip install -r requirements.txt
echo.
echo Backend running at: http://localhost:8000
echo API Docs at:        http://localhost:8000/docs
echo.
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
