@echo off
chcp 65001 >nul
cd /d "%~dp0"
title Laboratorio 01 - Ventas e Inventario

set PY=python
python --version >nul 2>&1 || set PY=py
%PY% --version >nul 2>&1 || (
  echo No se encontro Python. Instalelo desde https://www.python.org/downloads/
  echo y marque la casilla "Add Python to PATH" durante la instalacion.
  pause
  exit /b
)

%PY% -c "import flask" >nul 2>&1 || (
  echo Instalando Flask, solo la primera vez...
  %PY% -m pip install -r requirements.txt
)

echo.
echo La aplicacion se abrira en el navegador.
echo NO cierre esta ventana mientras la usa. Para detenerla, cierrela.
echo.
%PY% app.py
pause
