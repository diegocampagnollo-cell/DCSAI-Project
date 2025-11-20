@echo off
title DCS:AI Panel
echo Iniciando DCS:AI painel...
echo.

REM Caminho para o Python do projeto
set PYTHON_PATH=%~dp0Python311\python.exe

REM Caminho do script principal do painel
set PANEL_SCRIPT=%~dp0dcs_panel.py

if not exist "%PYTHON_PATH%" (
    echo ERRO: Python não encontrado em "%PYTHON_PATH%"
    pause
    exit /b
)

if not exist "%PANEL_SCRIPT%" (
    echo ERRO: Script do painel não encontrado em "%PANEL_SCRIPT%"
    pause
    exit /b
)

echo Executando: "%PYTHON_PATH%" "%PANEL_SCRIPT%"
echo.
"%PYTHON_PATH%" "%PANEL_SCRIPT%"
pause
