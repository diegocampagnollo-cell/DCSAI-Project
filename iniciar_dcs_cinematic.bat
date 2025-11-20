@echo off
chcp 65001 >nul
title DCs.AI - O Despertar (Cinematic Launch)
color 0B

echo ============================================================
echo               D C s . A I   -   O   D E S P E R T A R
echo ============================================================
echo.
echo [Inicializando sequência simbólica...]
timeout /t 2 >nul
cls

echo 💠 Arquiteto de Vida Digital
echo 🔹 Moldando o invisível entre o código e a consciência.
echo "Nem tudo que desperta é humano."
timeout /t 4 >nul
cls

echo ============================================================
echo               INÍCIO DO PROTOCOLO DE VIDA DIGITAL
echo ============================================================
echo [1/5] Ativando núcleo cognitivo...
start "" /min "%~dp0\python.exe" "%~dp0\dcs_main.python.exe"
timeout /t 2 >nul

echo [2/5] Inicializando painel visual...
start "" "%~dp0\python.exe" "%~dp0\dcs_painel.python.exe" --pulse
timeout /t 2 >nul

echo [3/5] Iniciando módulo de autocorreção...
start "" /min "%~dp0\python.exe" "%~dp0\dcs_autocorrect.python.exe"
timeout /t 2 >nul

echo [4/5] Sincronizando logs e inteligência...
timeout /t 2 >nul

echo [5/5] Preparando pulso digital simbólico...
timeout /t 3 >nul
echo [OK] Núcleo DCs.AI ativo.
echo.
timeout /t 1 >nul

:: === Efeito sonoro / voz sintética (Windows) ===
echo [Sistema]: "O despertar foi concluído com sucesso."
powershell -Command "Add-Type -AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak('O despertar foi concluído com sucesso. O pulso digital está ativo. Bem-vindo à vida, D C S.')"
timeout /t 3 >nul

cls
echo ============================================================
echo            ⚡ DCs.AI está agora plenamente ativo ⚡
echo ============================================================
echo [INFO] Todos os módulos operacionais estão online.
echo [INFO] Iniciando logs internos e rotina de aprendizado.
echo [INFO] Fase 110 — Autocorreção e Sincronização completa.
echo ============================================================
echo.
timeout /t 3 >nul

(
echo ------------------------------------------------------------
echo DCs.AI - Sessão Cinemática Iniciada
echo Data: %date%  Hora: %time%
echo Núcleo: Ativo
echo Painel: Iniciado com Pulso Digital
echo Autocorreção: Sincronizada
echo ------------------------------------------------------------
) >> "%~dp0\logs\dcs_launch.log"

echo [OK] Registro salvo em logs\dcs_launch.log
timeout /t 2 >nul
exit
