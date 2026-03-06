@echo off
echo Starting CryptoQuant AI Frontend...
cd /d %~dp0..\frontend
npm install
echo.
echo Frontend running at: http://localhost:3000
echo.
npm run dev
pause
