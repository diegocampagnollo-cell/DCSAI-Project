import customtkinter as ctk
import threading
import asyncio
import json
import socket
import time

# Configuração global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

HOST = "127.0.0.1"
PORT = 22888

class RPCClient:
    def __init__(self, log_func):
        self.log = log_func
        self.connected = False
        self.reader = None
        self.writer = None

    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(HOST, PORT)
            self.connected = True
            self.log(f"[CONNECTED] Connected to {HOST}:{PORT} ✅")
            await self.auth()
        except Exception as e:
            self.log(f"[ERROR] Connection failed: {e}")
            self.connected = False

    async def auth(self):
        try:
            msg = json.dumps({"type": "auth", "token": "panel_token"}) + "\n"
            self.writer.write(msg.encode())
            await self.writer.drain()
            self.log("[AUTH] Token sent to core.")

            while True:
                line = await self.reader.readline()
                if not line:
                    self.log("[WARN] Connection closed by core.")
                    self.connected = False
                    break
                data = json.loads(line.decode().strip())
                self.log(f"[RX] {data}")
        except Exception as e:
            self.log(f"[ERROR] {e}")
            self.connected = False

    async def send(self, payload):
        if not self.connected or not self.writer:
            self.log("[WARN] Not connected to core.")
            return
        msg = json.dumps(payload) + "\n"
        self.writer.write(msg.encode())
        await self.writer.drain()
        self.log(f"[TX] {payload}")

class PanelApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("⚡ DCs.AI Cyber Panel")
        self.geometry("900x600")

        self.client = RPCClient(self.log_message)
        self.loop = asyncio.new_event_loop()
        threading.Thread(target=self._run_loop, daemon=True).start()

        # Layout principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        title = ctk.CTkLabel(self, text="DCs.AI Cyber Panel", font=("Consolas", 26, "bold"), text_color="#00FFAA")
        title.grid(row=0, column=0, pady=(15, 5))

        # Botões
        button_frame = ctk.CTkFrame(self, fg_color="#111111", corner_radius=10)
        button_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(5, 10))
        button_frame.grid_columnconfigure((0, 1, 2), weight=1)

        self.btn_connect = ctk.CTkButton(button_frame, text="Conectar", fg_color="#00CC88", command=self._on_connect)
        self.btn_connect.grid(row=0, column=0, padx=10, pady=10)

        self.btn_ping = ctk.CTkButton(button_frame, text="Ping → Core", fg_color="#0088FF", command=self._on_ping)
        self.btn_ping.grid(row=0, column=1, padx=10, pady=10)

        self.btn_clear = ctk.CTkButton(button_frame, text="Limpar Logs", fg_color="#FF5500", command=self._on_clear)
        self.btn_clear.grid(row=0, column=2, padx=10, pady=10)

        # Caixa de logs
        self.log_box = ctk.CTkTextbox(self, width=880, height=400, fg_color="#0A0A0A", text_color="#00FFAA")
        self.log_box.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="nsew")
        self.log_box.insert("end", "🟢 Painel iniciado.\n")

    def _run_loop(self):
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def _on_connect(self):
        self.log_message("[INFO] Connecting to core...")
        asyncio.run_coroutine_threadsafe(self.client.connect(), self.loop)

    def _on_ping(self):
        asyncio.run_coroutine_threadsafe(
            self.client.send({"type": "ping", "time": time.time()}), self.loop
        )

    def _on_clear(self):
        self.log_box.delete("1.0", "end")
        self.log_message("🧹 Logs limpos.")

    def log_message(self, msg):
        self.log_box.insert("end", f"{msg}\n")
        self.log_box.see("end")

if __name__ == "__main__":
    app = PanelApp()
    app.mainloop()
