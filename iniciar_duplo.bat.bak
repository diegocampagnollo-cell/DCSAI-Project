@echo off
title DCs.AI - Inicialização automática (Visual)
color 0a

cd /d "C:\Users\DIEGO\Desktop\DCs_AI_vFinal"

echo ================================================
echo        INICIANDO DCS.AI - MODO DUPLO AUTOMATICO
echo ================================================
echo.

echo [1/3] Iniciando servidor (porta 22000)...
start "Servidor DCs.AI" cmd /k "python -m core.dcs_network_v2 --server --port 22000"

echo Aguardando inicializacao completa do servidor...
timeout /t 10 /nobreak >nul

echo [2/3] Iniciando cliente (conecta em 22000)...
start "Cliente DCs.AI" cmd /k "python -m core.dcs_network_v2 --client --port 22000"

timeout /t 3 /nobreak >nul

echo [3/3] Iniciando núcleo principal...
start "DCs.AI - MainCore" cmd /k "python dcs_main.py"

echo.
echo ================================================
echo Todos os módulos foram iniciados com sucesso.
echo As janelas abrirão automaticamente.
echo ================================================
pause
exit
