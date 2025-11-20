@echo off
title Iniciando DCS:AI - Core + Painel
color 0B

echo ==============================================
echo     INICIANDO DCS:AI CORE E PAINEL...
echo ==============================================

REM Abre o CORE
start "DCS:AI Core" cmd /k ""%~dp0Python311\python.exe" "%~dp0core\dcs_main.py""

REM Aguarda o Core subir antes do Painel
timeout /t 5 /nobreak >nul

REM Abre o PAINEL
start "DCS:AI Painel" cmd /k ""%~dp0Python311\python.exe" "%~dp0dcs_panel.py""

echo.
echo Core e Painel foram iniciados!
echo ==============================================
echo Para encerrar, feche as janelas abertas.
pause
