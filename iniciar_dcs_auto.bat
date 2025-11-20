@echo off
title DCS:AI Core
echo Iniciando DCS:AI core...
echo.

set PYTHON_PATH="%~dp0Python311\python.exe"
set CORE_PATH="%~dp0core\dcs_main.py"

if not exist %PYTHON_PATH% (
    echo ERRO: Python nao encontrado em %PYTHON_PATH%
    pause
    exit /b
)

if not exist %CORE_PATH% (
    echo ERRO: Core nao encontrado em %CORE_PATH%
    pause
    exit /b
)

echo Executando: %PYTHON_PATH% %CORE_PATH%
echo.
%PYTHON_PATH% %CORE_PATH%
pause
