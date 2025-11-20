# dcs_panel.py
# Executa a UI do painel e conecta ao core DCS.AI (socket client).
# Compatível com Python 3.11+

import os
import sys
import json
import logging
from pathlib import Path

# Ajusta imports relative do pacote ui
# Se executar a partir da raiz do projeto, isso garante import funcionar.
ROOT = Path(__file__).resolve().parent
UI_DIR = ROOT / "ui"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(UI_DIR) not in sys.path:
    sys.path.insert(0, str(UI_DIR))

try:
    from panel_ui import PanelUI
except Exception as e:
    print("Erro importando UI:", e)
    raise

# Configuração simples de logs
LOGS = ROOT / "logs"
LOGS.mkdir(exist_ok=True)
logging.basicConfig(
    filename=str(LOGS / "dcs_panel.log"),
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def main():
    logging.info("Iniciando DCS.AI Panel")
    ui = PanelUI(core_host="127.0.0.1", core_port=22000, log_dir=LOGS)
    try:
        ui.start()  # blocks until UI fechado
    except KeyboardInterrupt:
        logging.info("Panel encerrado por KeyboardInterrupt")
    except Exception:
        logging.exception("Erro inesperado no painel")
    finally:
        logging.info("Finalizando painel")

if __name__ == "__main__":
    main()
