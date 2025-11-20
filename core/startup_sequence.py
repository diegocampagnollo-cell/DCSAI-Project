# -*- coding: utf-8 -*-
"""
Script de inicialização que pode ser usado pelo .bat.
Ele apenas chama dcs_main (mesma lógica), mas mantido separado
para futuros fluxos (cinematic, híbrido, etc.).
"""
from .dcs_main import run_core


if __name__ == '__main__':
run_core()
