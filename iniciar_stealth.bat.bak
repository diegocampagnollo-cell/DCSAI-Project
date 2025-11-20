@echo off
title DCs.AI - Inicialização stealth (logs)
cd /d "C:\Users\DIEGO\Desktop\DCs_AI_vFinal"

if not exist logs mkdir logs

echo [%date% %time%] Starting stealth launcher...>> logs\startup.log

:: start server (background) - redirect stdout/stderr to log
start "Servidor (stealth)" /B cmd /c "python -u -m core.dcs_network_v2 --server --port 22000 >> logs\startup.log 2>&1"

timeout /t 10 /nobreak >nul

:: start client (background)
start "Cliente (stealth)" /B cmd /c "python -u -m core.dcs_network_v2 --client --port 22000 >> logs\startup.log 2>&1"

timeout /t 3 /nobreak >nul

:: start main core (background)
start "MainCore (stealth)" /B cmd /c "python -u dcs_main.py >> logs\startup.log 2>&1"

echo [%date% %time%] All processes started.>> logs\startup.log
echo Stealth start complete. Logs: logs\startup.log
exit
