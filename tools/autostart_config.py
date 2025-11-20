# -*- coding: utf-8 -*-
import os, sys, shutil, getpass, time
import winreg

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH = os.path.join(ROOT, "apply_patch.bat")  # or iniciar_dcs_automon.bat
LOG = os.path.join(ROOT, "logs", "autostart_setup.log")
os.makedirs(os.path.join(ROOT,"logs"), exist_ok=True)

# run minimized via cmd /c start /min "" "path\to\batch"
cmd = f'cmd /c start /min "" "{BATCH}" >> "{os.path.join(ROOT,"logs","startup.log")}" 2>&1'

try:
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
    winreg.SetValueEx(key, "DCS_AI_AutoStart", 0, winreg.REG_SZ, cmd)
    winreg.CloseKey(key)
    print("[OK] Autostart added to current user Run key.")
except Exception as e:
    print("[ERR] Could not add autostart:", e)
