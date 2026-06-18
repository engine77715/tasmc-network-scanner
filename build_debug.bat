@echo off
echo ============================================
echo   TASMC Network Scanner - DEBUG Build (with console)
echo ============================================
echo.

pyinstaller --onefile --name "TASMC_Network_Scanner_DEBUG" main.py

echo.
echo ============================================
echo   Done! Run dist\TASMC_Network_Scanner_DEBUG.exe
echo   from a terminal to see console output.
echo ============================================
pause