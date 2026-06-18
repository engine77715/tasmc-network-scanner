@echo off
echo ============================================
echo   TASMC Network Scanner - Build EXE
echo ============================================
echo.

pyinstaller --onedir --windowed --name "TASMC_Network_Scanner" main.py

echo.
echo ============================================
echo   Done! Check dist\TASMC_Network_Scanner\
echo   Run TASMC_Network_Scanner.exe from inside that folder.
echo ============================================
pause