@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title DCS.AI - Auto Fix Path (Final)
color 0A

set "basepath=%~dp0"
if not exist "%basepath%logs" mkdir "%basepath%logs"
set "logfile=%basepath%logs\apply_fix.log"

echo =============================================================== > "%logfile%"
echo [INICIO] Corrigindo caminhos em %date% %time% >> "%logfile%"
echo Basepath: %basepath% >> "%logfile%"
echo =============================================================== >> "%logfile%"
echo.

:: Detectar Python
set "pythonpath=%LocalAppData%\Programs\Python\Python311\python.exe"
if not exist "%pythonpath%" set "pythonpath=%basepath%Python311\python.exe"

if not exist "%pythonpath%" (
    echo [ERRO] Python 3.11 não encontrado.
    echo [ERRO] Python 3.11 não encontrado. >> "%logfile%"
    pause
    exit /b
)

echo [OK] Python detectado em: %pythonpath%
echo [OK] Python detectado em: %pythonpath% >> "%logfile%"
echo.

:: Corrigir .bat
for %%f in ("%basepath%*.bat") do (
    if /I not "%%~nxf"=="apply_fix_path.bat" (
        echo [INFO] Corrigindo: %%~nxf
        echo [INFO] Corrigindo: %%~nxf >> "%logfile%"
        copy /Y "%%~f" "%%~f.bak" >nul
        powershell -Command ^
        "$c=(Get-Content '%%~f'); $c -replace 'python.*\.exe','\"%pythonpath%\"' | Set-Content '%%~f'" 2>> '%logfile%'
    )
)

echo.
echo ===============================================================
echo [SUCESSO] Caminhos corrigidos com backups (.bak)
echo Log salvo em: logs\apply_fix.log
echo ===============================================================
pause
exit
