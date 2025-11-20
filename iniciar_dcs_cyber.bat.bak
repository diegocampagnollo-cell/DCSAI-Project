@echo off
chcp 65001 >nul
rem Start core (top) and panel (bottom) - horizontal stacking is left to the window manager.
cd /d "%~dp0\core"
start "DCs.AI Core" cmd /k "cd /d \"%~dp0core\" && python -m core.dcs_main"
start "DCs.AI Panel" cmd /k "cd /d \"%~dp0core\" && python -m core.dcs_panel"
exit /b 0
