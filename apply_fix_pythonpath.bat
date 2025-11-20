@echo off
title DCS.AI - Python Path Fix (Auto)
echo ===============================
echo Corrigindo caminhos do Python...
echo ===============================
echo.

REM Define a variável da pasta principal
set "BASE_DIR=%~dp0"

REM Verifica se o Python existe dentro da pasta Python311
if exist "%BASE_DIR%Python311\python.exe" (
    echo Python encontrado em "%BASE_DIR%Python311\python.exe"
) else (
    echo ERRO: Python nao encontrado em "%BASE_DIR%Python311"
    pause
    exit /b
)

REM Ajusta o PATH temporariamente
setx PATH "%BASE_DIR%Python311;%BASE_DIR%Python311\Scripts;%PATH%"

echo.
echo Caminhos ajustados com sucesso!
echo.
pause
exit /b
