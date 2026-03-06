@echo off
echo ============================================
echo  CryptoQuant AI Platform - Version Checker
echo ============================================
echo.
echo [Python Versions Available]
python --version 2>nul || echo   python: not in PATH
py -3.11 --version 2>nul || echo   Python 3.11: not found
py -3.12 --version 2>nul || echo   Python 3.12: not found
py -3.14 --version 2>nul || echo   Python 3.14: not found (pre-release)
echo.
echo [pip]
pip --version 2>nul
echo.
echo [Node.js and npm]
node --version 2>nul || echo   node: not found
npm --version 2>nul || echo   npm: not found
echo.
echo ============================================
echo  RECOMMENDED: Python 3.11 or 3.12
echo  NOTE: Python 3.14 is pre-release, not stable
echo  USE: py -3.11 -m uvicorn backend.main:app ...
echo ============================================
pause
