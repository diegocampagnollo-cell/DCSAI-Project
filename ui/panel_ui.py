# ui/panel_ui.py
# Painel visual (Tkinter) + cliente socket em thread.
# Mantido simples e robusto: reconecta automaticamente e atualiza labels.

import socket
import threading
import time
import json
import queue
import logging
from pathlib import Path
import tkinter as tk
from tkinter import ttk

# estilo Cyber Blue (cores simples)
_BG = "#0b1220"
_PANEL = "#0f2340"
_TEXT = "#cde8ff"
_ACCENT = "#00aaff"

class NetworkClient(threading.Thread):
    """Thread que conecta no core e coloca mensagens decodificadas na fila."""
    def __init__(self, host, port, out_q, stop_event, reconnect=2.0):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.out_q = out_q
        self.stop_event = stop_event
        self.reconnect_delay = reconnect
        self.sock = None

    def run(self):
        while not self.stop_event.is_set():
            try:
                self._connect_and_listen()
            except Exception as e:
                logging.exception("Network client erro: %s", e)
            if self.stop_event.is_set():
                break
            time.sleep(self.reconnect_delay)

    def _connect_and_listen(self):
        logging.info("Tentando conectar em %s:%s", self.host, self.port)
        with socket.create_connection((self.host, self.port), timeout=5) as s:
            s.settimeout(1.0)
            self.sock = s
            logging.info("Conectado ao core")
            buffer = b""
            while not self.stop_event.is_set():
                try:
                    data = s.recv(4096)
                    if not data:
                        logging.info("Socket fechado pelo host")
                        break
                    buffer += data
                    # processa por linhas (JSON por linha) ou tenta decodificar direto
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        self._handle_line(line)
                except socket.timeout:
                    continue
                except Exception as e:
                    logging.exception("Erro lendo socket: %s", e)
                    break
            logging.info("Saindo do loop de leitura")

    def _handle_line(self, line):
        try:
            text = line.decode(errors="replace").strip()
            if not text:
                return
            # tenta JSON primeiro
            try:
                payload = json.loads(text)
                self.out_q.put(payload)
            except Exception:
                # tenta parse simples "key=value" ou texto livre
                self.out_q.put({"raw": text})
        except Exception:
            logging.exception("Erro processando linha recebida")

    def stop(self):
        self.stop_event.set()
        try:
            if self.sock:
                self.sock.close()
        except Exception:
            pass

class PanelUI:
    def __init__(self, core_host="127.0.0.1", core_port=22000, log_dir: Path|str = None):
        self.core_host = core_host
        self.core_port = core_port
        self.log_dir = Path(log_dir) if log_dir else None

        # logging minimal
        logging.basicConfig(
            filename=str(self.log_dir / "panel_ui.log") if self.log_dir else None,
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

        self.root = tk.Tk()
        self.root.title("DCs.AI - Painel Vivo (Cyber Blue)")
        self.root.configure(bg=_BG)
        # build UI
        self._build_ui()

        # networking
        self.msg_q = queue.Queue()
        self.stop_event = threading.Event()
        self.net = NetworkClient(self.core_host, self.core_port, self.msg_q, self.stop_event)
        self.net.start()

        # schedule UI polling
        self._polling_interval_ms = 250
        self.root.after(self._polling_interval_ms, self._poll_network)

        # graceful close
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        pad = 12
        frame = ttk.Frame(self.root, padding=pad)
        frame.pack(fill="both", expand=True)
        style = ttk.Style()
        style.theme_use("clam")
        # Style colors
        style.configure("TFrame", background=_BG)
        style.configure("Card.TFrame", background=_PANEL, relief="flat")
        style.configure("TLabel", background=_PANEL, foreground=_TEXT, font=("Consolas", 11))
        style.configure("Title.TLabel", background=_PANEL, foreground=_ACCENT, font=("Consolas", 16, "bold"))
        style.configure("Value.TLabel", background=_PANEL, foreground=_TEXT, font=("Consolas", 20, "bold"))

        # container
        container = ttk.Frame(frame, style="TFrame")
        container.pack(fill="both", expand=True)

        # top title
        title = ttk.Label(container, text="DCs.AI - Painel Vivo", style="Title.TLabel")
        title.pack(pady=(0,10))

        # metrics cards
        cards = ttk.Frame(container, style="TFrame")
        cards.pack(fill="x", padx=10)

        # CPU card
        self.cpu_card = ttk.Frame(cards, style="Card.TFrame", padding=10)
        self.cpu_card.pack(side="left", padx=8, pady=4)
        ttk.Label(self.cpu_card, text="CPU", style="TLabel").pack()
        self.cpu_val = ttk.Label(self.cpu_card, text="-- %", style="Value.TLabel")
        self.cpu_val.pack()

        # MEM card
        self.mem_card = ttk.Frame(cards, style="Card.TFrame", padding=10)
        self.mem_card.pack(side="left", padx=8, pady=4)
        ttk.Label(self.mem_card, text="MEM", style="TLabel").pack()
        self.mem_val = ttk.Label(self.mem_card, text="-- %", style="Value.TLabel")
        self.mem_val.pack()

        # TEMP card
        self.temp_card = ttk.Frame(cards, style="Card.TFrame", padding=10)
        self.temp_card.pack(side="left", padx=8, pady=4)
        ttk.Label(self.temp_card, text="TEMP", style="TLabel").pack()
        self.temp_val = ttk.Label(self.temp_card, text="-- °C", style="Value.TLabel")
        self.temp_val.pack()

        # STATUS card
        self.st_card = ttk.Frame(cards, style="Card.TFrame", padding=10)
        self.st_card.pack(side="left", padx=8, pady=4)
        ttk.Label(self.st_card, text="STATUS", style="TLabel").pack()
        self.st_val = ttk.Label(self.st_card, text="idle", style="Value.TLabel")
        self.st_val.pack()

        # bottom small log area
        self.log_text = tk.Text(container, height=6, bg=_BG, fg=_TEXT, bd=0, padx=8, pady=6)
        self.log_text.pack(fill="both", expand=False, padx=10, pady=(12,0))
        self.log_text.insert("end", "Iniciando painel...\n")
        self.log_text.configure(state="disabled")

        # window sizing and center
        self.root.geometry("520x360")
        self.root.minsize(420, 300)

    def _poll_network(self):
        updated = False
        while True:
            try:
                msg = self.msg_q.get_nowait()
            except queue.Empty:
                break
            try:
                self._process_message(msg)
                updated = True
            except Exception:
                logging.exception("Erro processando mensagem do core: %s", msg)
        if updated:
            self._append_log("Mensagem recebida e UI atualizada")
        # re-schedule
        if not self.stop_event.is_set():
            self.root.after(self._polling_interval_ms, self._poll_network)

    def _process_message(self, msg):
        # msg pode ser dicionario parseado do JSON ou {"raw": "..."}
        if not isinstance(msg, dict):
            return
        cpu = msg.get("cpu")
        mem = msg.get("mem")
        temp = msg.get("temp")
        status = msg.get("status")

        # fallback se veio em texto livre com "cpu=11.1 mem=59"
        if "raw" in msg and isinstance(msg["raw"], str):
            txt = msg["raw"]
            try:
                for part in txt.replace(",", " ").split():
                    if "=" in part:
                        k, v = part.split("=",1)
                        k = k.lower()
                        try:
                            val = float(v)
                        except:
                            val = v
                        if k == "cpu": cpu = val
                        if k == "mem": mem = val
                        if k == "temp": temp = val
                        if k == "status": status = v
            except Exception:
                pass

        # Atualiza labels de forma segura (formatters)
        if cpu is not None:
            try:
                self.cpu_val.config(text=f"{float(cpu):.1f} %")
            except Exception:
                self.cpu_val.config(text=str(cpu))
        if mem is not None:
            try:
                self.mem_val.config(text=f"{float(mem):.1f} %")
            except Exception:
                self.mem_val.config(text=str(mem))
        if temp is not None:
            try:
                self.temp_val.config(text=f"{float(temp):.1f} °C")
            except Exception:
                self.temp_val.config(text=str(temp))
        if status is not None:
            self.st_val.config(text=str(status))

    def _append_log(self, line):
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"{time.strftime('%H:%M:%S')} {line}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")

    def _on_close(self):
        logging.info("Fechando painel - solicitando parada da rede")
        self.stop_event.set()
        try:
            self.net.stop()
        except Exception:
            pass
        # agenda fechamento após curto delay para garantir shutdown
        self.root.after(250, self.root.destroy)

    def start(self):
        self._append_log("Conectando ao core %s:%s" % (self.core_host, self.core_port))
        self.root.mainloop()
