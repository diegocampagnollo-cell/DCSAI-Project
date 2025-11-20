@echo off
title DCs.AI - Modo Teste Contínuo
cd /d "C:\Users\DIEGO\Desktop\DCs_AI_vFinal"

if not exist logs mkdir logs

:loop
echo [%date% %time%] Starting test loop...>> logs\startup.log

:: Start server
start "Servidor-Test" cmd /k "python -m core.dcs_network_v2 --server --port 22000"
timeout /t 8 /nobreak >nul

:: Start client
start "Cliente-Test" cmd /k "python -m core.dcs_network_v2 --client --port 22000"
timeout /t 4 /nobreak >nul

:: Start core
start "Core-Test" cmd /k "python dcs_main.py"
timeout /t 10 /nobreak >nul

:: Wait and then restart cycle (adjust as needed)
echo [%date% %time%] Cycle complete. Waiting 60s before next cycle...>> logs\startup.log
timeout /t 60 /nobreak >nul

goto loop
