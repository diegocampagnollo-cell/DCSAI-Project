import tkinter as tk
import customtkinter as ctk
import math
import time
import os
import logging
from logging.handlers import RotatingFileHandler
import threading

# ==========================================================
# CONFIGURAÇÕES
# ==========================================================
PANEL_BG = "#000000"
RADAR_COLOR = "#00FF9C"
TEXT_COLOR = "#00FF9C"
LOG_FONT = ("Consolas", 12)

# ==========================================================
# LOGGING SETUP
# ==========================================================
def setup_logger(callback=None):
    os.makedirs("logs", exist_ok=True)
    logger = logging.getLogger("RadarLogger")
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers
    if logger.handlers:
        for h in logger.handlers[:]:
            logger.removeHandler(h)

    # Arquivo rotativo
    file_handler = RotatingFileHandler("logs/radar.log", maxBytes=300_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", "%H:%M:%S"))
    logger.addHandler(file_handler)

    # Console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(console_handler)

    # Interface callback (texto em tempo real)
    if callback:
        class TextHandler(logging.Handler):
            def emit(self, record):
                msg = self.format(record)
                callback(msg)
        text_handler = TextHandler()
        text_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(text_handler)

    return logger


# ==========================================================
# RADAR VISUAL
# ==========================================================
class EnergyRadar(ctk.CTkCanvas):
    def __init__(self, master, size=400, bg=PANEL_BG, color=RADAR_COLOR):
        super().__init__(master, width=size, height=size, bg=bg, highlightthickness=0)
        self.size = size
        self.color = color
        self.angle = 0
        self.running = True
        self.draw_static()
        self.after(10, self.animate)

    def draw_static(self):
        self.delete("circles")
        for i in range(1, 6):
            r = i * (self.size // 6)
            self.create_oval(
                self.size/2 - r, self.size/2 - r,
                self.size/2 + r, self.size/2 + r,
                outline=self.color, width=1, tags="circles"
            )

    def animate(self):
        self.delete("beam")
        length = self.size / 2.1
        end_x = self.size / 2 + math.cos(math.radians(self.angle)) * length
        end_y = self.size / 2 + math.sin(math.radians(self.angle)) * length
        self.create_line(
            self.size/2, self.size/2, end_x, end_y,
            fill=self.color, width=2, tags="beam"
        )
        self.angle = (self.angle + 2) % 360
        if self.running:
            self.after(30, self.animate)


# ==========================================================
# APP PRINCIPAL
# ==========================================================
class PanelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DCs_AI Cyber Panel")
        self.geometry("1150x650")
        self.configure(fg_color=PANEL_BG)
        self._build_ui()

        # Inicializa logger com callback para log_text
        global log
        log = setup_logger(self._append_log)
        log.info("Interface iniciada com sucesso.")
        log.info("Radar verde-esmeralda pronto para operação.")

    def _build_ui(self):
        # TOPO
        topbar = ctk.CTkFrame(self, fg_color=PANEL_BG)
        topbar.pack(fill="x", padx=10, pady=5)

        self.ip_entry = ctk.CTkEntry(topbar, width=150, placeholder_text="127.0.0.1")
        self.ip_entry.pack(side="left", padx=5)

        self.port_entry = ctk.CTkEntry(topbar, width=80, placeholder_text="5050")
        self.port_entry.pack(side="left", padx=5)

        self.connect_button = ctk.CTkButton(topbar, text="Conectar", command=self.connect_server)
        self.connect_button.pack(side="left", padx=5)

        self.status_label = ctk.CTkLabel(topbar, text="Status: Desconectado", text_color="gray")
        self.status_label.pack(side="left", padx=10)

        # CONTAINER PRINCIPAL
        main_frame = ctk.CTkFrame(self, fg_color=PANEL_BG)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # RADAR
        self.radar = EnergyRadar(main_frame, size=450, bg=PANEL_BG)
        self.radar.pack(side="left", padx=10, pady=10)

        # LOG AREA
        log_frame = ctk.CTkFrame(main_frame, fg_color="#050505", corner_radius=10)
        log_frame.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        log_label = ctk.CTkLabel(log_frame, text="📡 LOGS DO SISTEMA", text_color=TEXT_COLOR, font=("Consolas", 16, "bold"))
        log_label.pack(anchor="w", padx=10, pady=(5, 0))

        self.log_text = tk.Text(
            log_frame, bg="#050505", fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR, relief="flat", font=LOG_FONT,
            wrap="word", state="disabled"
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Barra de rolagem
        scrollbar = tk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scrollbar.set)

    # =====================================================
    # FUNÇÕES DE LOG
    # =====================================================
    def _append_log(self, message):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    # =====================================================
    # FUNÇÕES DE CONEXÃO
    # =====================================================
    def connect_server(self):
        ip = self.ip_entry.get()
        port = self.port_entry.get()
        log.info(f"Tentando conectar a {ip}:{port} ...")

        threading.Thread(target=self._simulate_connection, args=(ip, port), daemon=True).start()

    def _simulate_connection(self, ip, port):
        time.sleep(1.5)
        self.status_label.configure(text=f"Status: Conectado ({ip}:{port})", text_color="lime")
        log.info(f"Conectado com sucesso ao servidor {ip}:{port}.")
        log.info("Iniciando varredura do radar...")

# ==========================================================
# ENTRY POINT
# ==========================================================
if __name__ == "__main__":
    log = setup_logger()
    log.info("Iniciando DCs_AI Cyber Panel...")
    app = PanelApp()
    try:
        app.mainloop()
    except Exception as e:
        log.error(f"Erro fatal: {e}")
    finally:
        log.info("Aplicação encerrada.")
