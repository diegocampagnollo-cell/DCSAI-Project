@echo off
chcp 65001 >nul
title DCS.AI - Sistema de Inicialização Autônoma (vFinal)
color 0A

echo ============================================================
echo             SISTEMA DE INICIALIZACAO DCS.AI (vFinal)
echo ============================================================
echo.

:: === Som de inicialização ===
if exist "%~dp0Startup.wav" (
    powershell -c "(New-Object Media.SoundPlayer '%~dp0Startup.wav').PlaySync()"
) else (
    echo [WARN] Arquivo de som Startup.wav não encontrado.
)
echo.

:: === Verificação da estrutura ===
echo [INFO] Verificando estrutura principal do DCS.AI...
timeout /t 2 >nul
echo [OK] Estrutura principal verificada.
echo ============================================================
echo.

:: === Seleção de modo de inicialização ===
echo Escolha o modo de inicializacao:
echo [1] Normal (com janelas e logs visuais)
echo [2] Silencioso (execucao em background)
echo ============================================================
set /p modo="Digite o numero do modo desejado: "

if "%modo%"=="1" goto normal
if "%modo%"=="2" goto silencioso

echo [ERRO] Opcao invalida. Encerrando...
timeout /t 3 >nul
exit /b

:normal
echo.
echo [INFO] Iniciando sequencia principal...
timeout /t 1 >nul
start "DCS.AI Core" cmd /k "%~dp0Python314\python.exe" "%~dp0dcs_main.py"
timeout /t 1 >nul
start "DCS.AI Panel" cmd /k "%~dp0Python314\python.exe" "%~dp0dcs_panel.py"
timeout /t 1 >nul
start "DCS.AI Autocorrect" cmd /k "%~dp0Python314\python.exe" "%~dp0dcs_autocorrect.py"
echo.
echo [OK] Sistema principal iniciado com sucesso.
goto fim

:silencioso
echo.
echo [INFO] Iniciando em modo silencioso (background)...
timeout /t 1 >nul
start "" /min "%~dp0Python314\python.exe" "%~dp0dcs_main.py"
start "" /min "%~dp0Python314\python.exe" "%~dp0dcs_panel.py"
start "" /min "%~dp0Python314\python.exe" "%~dp0dcs_autocorrect.py"
echo [OK] Execucao em segundo plano iniciada.
goto fim

:fim
echo ============================================================
echo Sistema de inicializacao concluido.
echo Pressione qualquer tecla para sair...
pause >nul
exit
