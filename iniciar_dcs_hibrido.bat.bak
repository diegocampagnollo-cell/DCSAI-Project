@echo off
title DCs.AI - Híbrido (core + painel)
rem -> ajusta charset do terminal (opcional)
chcp 65001 >nul

rem -> abre terminal para o core (módulos)
start "DCs.AI Core" cmd /k "cd /d \"%~dp0core\" && python -m core.dcs_main"

rem -> abre terminal para o painel (visual)
start "DCs.AI Painel" cmd /k "cd /d \"%~dp0core\" && python -m core.dcs_panel"

exit /b 0
