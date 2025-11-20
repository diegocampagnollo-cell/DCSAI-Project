DCs.AI - Painel Vivo (Cyber Blue) - Pacote Final
-------------------------------------------------
Como executar (Windows):
  1. Extraia o ZIP para uma pasta (ex: C:\Users\DIEGO\Desktop\DCS_AI_Final)
  2. Abra a pasta e dê um duplo-clique em iniciar_dcs.bat
     - Isso abrirá duas janelas: Core (módulos) e Panel (interface visual).
  3. Dependências opcionais (para leituras reais):
     python -m pip install --user psutil
  4. Se quiser rodar manualmente:
     python dcs_main.py   # inicia core (monitor + autocorrect)
     python dcs_panel.py  # abre o painel visual (Tkinter)
Notas:
  - O painel tenta usar psutil para dados reais e cai para simulacões caso não esteja instalado.
  - Logs são gravados em ./logs/dcs_log.txt e o status do painel em ./data/panel_status.json
