@echo off
chcp 65001 >nul
echo Applying DCS_AI patch...
REM backup_and_replace script will copy from core_patch into core (if used)
python -u tools\backup_and_replace.py
echo Patch applied.
pause
