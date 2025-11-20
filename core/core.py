# core/core.py
import os
import time
from datetime import datetime


class DCsCore:
    """Classe principal do núcleo DCs.AI"""
    def __init__(self):
        self.status = "inicializando"
        self.start_time = datetime.now()
        self.log_file = os.path.join("logs", "core.log")
        os.makedirs("logs", exist_ok=True)
        self.log("DCsCore inicializado.")

    def log(self, msg: str, level: str = "INFO"):
        ts = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{ts}] [{level}] {msg}"
        print(log_msg)
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(log_msg + "\n")

    def get_status(self):
        uptime = datetime.now() - self.start_time
        return {
            "status": self.status,
            "uptime": str(uptime).split(".")[0],
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def run_cycle(self):
        """Simula alguma atividade do core"""
        self.log("Executando ciclo principal...")
        time.sleep(1)
        self.log("Ciclo concluído.")


if __name__ == "__main__":
    core = DCsCore()
    core.run_cycle()
