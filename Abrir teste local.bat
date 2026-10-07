@echo off
cd /d "%~dp0"
python local_server.py
if errorlevel 1 (
  echo.
  echo Nao consegui iniciar o teste. Confira se o Python esta instalado.
  pause
)
