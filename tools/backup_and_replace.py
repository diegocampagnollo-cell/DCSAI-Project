# -*- coding: utf-8 -*-
import os, shutil
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORE = os.path.join(ROOT, "core")
PATCH = os.path.join(ROOT, "core_patch")  # if you keep patch files in core_patch
BACKUP = os.path.join(CORE, "backup_core")
os.makedirs(BACKUP, exist_ok=True)

files = ["dcs_main.py","dcs_network_v2.py","dcs_state_sync.py"]
for fn in files:
    src = os.path.join(CORE, fn)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(BACKUP, fn))
    patch_src = os.path.join(PATCH, fn)
    if os.path.exists(patch_src):
        shutil.copy2(patch_src, src)

print("[OK] backup applied and patched files copied.")
