@echo off
cd /d "%~dp0"
echo Starting DCs.AI Core...
start "DCs.AI Core" cmd /k "python dcs_main.py"
timeout /t 1 >nul
echo Starting DCs.AI Panel...
start "DCs.AI Panel" cmd /k "python dcs_panel.py"
exit
