@echo off
chcp 65001 >nul
title DCS_AI - Patch Seguro com Verificação
echo ============================================================
echo      DCs.AI Patch Seguro com Backup e Confirmacao
echo ============================================================
echo.
echo Este processo ira:
echo  - Fazer backup dos arquivos originais em core\backup_core
echo  - Exibir diferencas detectadas antes de sobrescrever
echo  - Permitir confirmar (Y/N) antes de aplicar
echo ------------------------------------------------------------
echo.
set /p confirm="Deseja continuar? (Y/N): "
if /I not "%confirm%"=="Y" (
    echo Operacao cancelada pelo usuario.
    pause
    exit /b
)

echo.
echo [1] Criando pasta de backup...
python - <<END
import os, shutil, filecmp
ROOT = os.path.dirname(__file__)
core = os.path.join(ROOT, "core")
backup = os.path.join(core, "backup_core")
patch = os.path.join(ROOT, "core_patch") if os.path.exists(os.path.join(ROOT,"core_patch")) else core
os.makedirs(backup, exist_ok=True)
files = ["dcs_main.py","dcs_network_v2.py","dcs_state_sync.py"]

for fn in files:
    src = os.path.join(core, fn)
    dst = os.path.join(patch, fn)
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(backup, fn))
        print(f"Backup criado: {fn}")
    if os.path.exists(dst):
        same = filecmp.cmp(src, dst, shallow=False) if os.path.exists(src) else False
        print(f"\nArquivo: {fn}")
        print("→ Arquivo destino:", dst)
        print("→ Arquivo original:", src)
        print("Status:", "IGUAL" if same else "DIFERENTE")
        if not same:
            print("Substituicao recomendada.")
END

echo.
set /p apply="Aplicar substituicoes agora? (Y/N): "
if /I not "%apply%"=="Y" (
    echo Operacao cancelada.
    pause
    exit /b
)

echo.
echo [2] Aplicando substituicoes...
python - <<END
import os, shutil
ROOT = os.path.dirname(__file__)
core = os.path.join(ROOT, "core")
patch = os.path.join(ROOT, "core_patch") if os.path.exists(os.path.join(ROOT,"core_patch")) else core
files = ["dcs_main.py","dcs_network_v2.py","dcs_state_sync.py"]
for fn in files:
    dst = os.path.join(core, fn)
    src = os.path.join(patch, fn)
    if os.path.exists(src):
        shutil.copy2(src, dst)
        print(f"Substituido: {fn}")
END

echo.
echo Patch aplicado com sucesso e backup salvo em core\backup_core\
echo ------------------------------------------------------------
pause
