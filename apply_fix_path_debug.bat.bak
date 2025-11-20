@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title DCS.AI - Auto Fix Path (Debug vFinal)
color 0A

:: === Diretório base ===
set "basepath=%~dp0"
if not exist "%basepath%logs" mkdir "%basepath%logs"

:: === Arquivo de log ===
set "logfile=%basepath%logs\apply_fix.log"
echo =============================================================== > "%logfile%"
echo [INICIO] Corrigindo caminhos em %date% %time% >> "%logfile%"
echo Basepath: %basepath% >> "%logfile%"
echo =============================================================== >> "%logfile%"
echo.

:: === Detectar Python ===
set "pythonpath=%LocalAppData%\Programs\Python\Python311\python.exe"
if not exist "%pythonpath%" (
    set "pythonpath=%basepath%Python311\python.exe"
)

if not exist "%pythonpath%" (
    echo [ERRO] Python 3.11 não encontrado.
    echo [ERRO] Python 3.11 não encontrado. >> "%logfile%"
    echo Verifique se ele existe em: >> "%logfile%"
    echo   %LocalAppData%\Programs\Python\Python311\python.exe >> "%logfile%"
    echo ou em: >> "%logfile%"
    echo   %basepath%Python311\python.exe >> "%logfile%"
    echo.
    echo Pressione qualquer tecla para sair...
    pause >nul
    exit /b
)

echo [OK] Python detectado em:
echo %pythonpath%
echo [OK] Python detectado em: %pythonpath% >> "%logfile%"
echo.

:: === Corrigir todos os .bat da pasta ===
for %%f in ("%basepath%*.bat") do (
    if not "%%~nxf"=="apply_fix_path.bat" (
        echo [INFO] Corrigindo: %%~nxf
        echo [INFO] Corrigindo: %%~nxf >> "%logfile%"
        copy /Y "%%~f" "%%~f.bak" >nul
        powershell -Command ^
        "(Get-Content '%%~f') -replace 'python.*\.exe', '%pythonpath%' | Set-Content '%%~f'" 2>> '%logfile%'
    )
)

echo.
echo ===============================================================
echo [SUCESSO] Caminhos corrigidos com backups (.bak)
echo Log salvo em: logs\apply_fix.log
echo ===============================================================
echo.
pause
exit
