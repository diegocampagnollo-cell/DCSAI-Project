@echo off
title DCs.AI - Núcleo + Painel
cd /d "C:\Users\DIEGO\Desktop\DCS_AI_vFinal"

echo ============================================
echo   Iniciando DCs.AI Core + Painel Visual
echo ============================================

REM --- Inicia o core em nova janela ---
start "DCs.AI Core" cmd /k "python core\main.py"

REM --- Aguarda 3 segundos pro core subir ---
timeout /t 3 /nobreak >nul

REM --- Inicia o painel visual ---
start "Painel DCs.AI" cmd /k "cd ui && python rpc_panel_gui.py"

echo.
echo Tudo iniciado! Feche esta janela se quiser manter apenas as outras.
pause
