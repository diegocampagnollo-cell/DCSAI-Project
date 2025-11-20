import tkinter as tk
import sys
import threading
import time
import os

modo_pulso = "--pulse" in sys.argv
status_path = os.path.join("logs", "dcs_status.txt")

def ler_status():
    if os.path.exists(status_path):
        with open(status_path, "r", encoding="utf-8") as f:
            return f.read().strip()
    return "repouso"

def animar_pulso(canvas, circulo):
    brilho = 100
    direcao = 1
    cor_atual = "#0000ff"

    while True:
        status = ler_status()

        # Define cor e velocidade conforme status
        if status == "repouso":
            cor_base = (0, 0, 255)
            delay = 0.05
        elif status == "processando":
            cor_base = (255, 255, 0)
            delay = 0.02
        elif status == "erro":
            cor_base = (255, 0, 0)
            delay = 0.01
        else:
            cor_base = (0, 255, 255)
            delay = 0.04

        # Cálculo de brilho e cor
        cor = f"#{int(cor_base[0]*brilho/255):02x}{int(cor_base[1]*brilho/255):02x}{int(cor_base[2]*brilho/255):02x}"
        canvas.itemconfig(circulo, fill=cor)

        brilho += direcao * 5
        if brilho >= 255:
            direcao = -1
        elif brilho <= 80:
            direcao = 1
        time.sleep(delay)

root = tk.Tk()
root.title("DCs.AI - Núcleo Visual")

canvas = tk.Canvas(root, width=400, height=400, bg="black", highlightthickness=0)
canvas.pack(expand=True, fill="both")

if modo_pulso:
    circulo = canvas.create_oval(150, 150, 250, 250, fill="#0000ff", outline="")
    threading.Thread(target=animar_pulso, args=(canvas, circulo), daemon=True).start()

label = tk.Label(root, text="💠 DCs.AI - Núcleo Ativo", fg="white", bg="black", font=("Consolas", 14))
label.pack(side="bottom", pady=10)

root.mainloop()
