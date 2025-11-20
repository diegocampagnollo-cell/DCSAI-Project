import tkinter as tk
import asyncio
import websockets
import json
import threading

HOST = "localhost"
PORT = 8765
WS_URL = f"ws://{HOST}:{PORT}"

# ===========================================================
# Funções de GUI
# ===========================================================

def add_log(text):
    log_box.config(state="normal")
    log_box.insert(tk.END, text + "\n")
    log_box.see(tk.END)
    log_box.config(state="disabled")

def update_stats(cpu, ram):
    cpu_label.config(text=f"CPU: {cpu}%")
    ram_label.config(text=f"RAM: {ram}%")


# ===========================================================
# Loop WebSocket em thread separada
# ===========================================================

async def websocket_loop():
    while True:
        try:
            add_log("[Painel] Conectando ao servidor...")
            async with websockets.connect(WS_URL) as ws:

                add_log("[Painel] Conectado com sucesso!")
                add_log("Aguardando mensagens...\n")

                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)

                    mtype = data.get("type")

                    if mtype == "stats":
                        cpu = data.get("cpu")
                        ram = data.get("ram")
                        message = data.get("message", "")

                        # Atualiza GUI de CPU e RAM
                        window.after(0, update_stats, cpu, ram)

                        # Log opcional
                        add_log(f"[Heartbeat] CPU={cpu}%  RAM={ram}%")

                    else:
                        # Qualquer outra mensagem vira log
                        add_log(f"[MSG] {data}")

        except Exception as e:
            add_log(f"[ERRO] {e}")
            add_log("Tentando reconectar em 3s...\n")
            await asyncio.sleep(3)


# ===========================================================
# Thread para rodar o asyncio
# ===========================================================

def start_async_loop():
    asyncio.run(websocket_loop())


# ===========================================================
# GUI Tkinter
# ===========================================================

window = tk.Tk()
window.title("DCs.AI - Painel de Logs em Tempo Real")
window.geometry("500x600")

# Título
title = tk.Label(window, text="Painel de Telemetria - DCs.AI", font=("Arial", 16, "bold"))
title.pack(pady=10)

# Stats CPU / RAM
cpu_label = tk.Label(window, text="CPU: --%", font=("Arial", 14))
cpu_label.pack()

ram_label = tk.Label(window, text="RAM: --%", font=("Arial", 14))
ram_label.pack()

# Caixa de logs
log_box = tk.Text(window, height=25, state="disabled", bg="#1e1e1e", fg="#00ff00")
log_box.pack(fill="both", expand=True, padx=10, pady=10)

# Iniciar WebSocket em outra thread
threading.Thread(target=start_async_loop, daemon=True).start()

window.mainloop()
