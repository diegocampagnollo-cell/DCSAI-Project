import asyncio
import random

class SynapseNode:
    def __init__(self, core, adaptive=False):
        self.core = core
        self.adaptive = adaptive
        self.running = False

    async def start(self):
        self.running = True
        print(f"🧠 Synapse Node ativo (modo adaptativo: {self.adaptive})")
        while self.running:
            await asyncio.sleep(3)
            if self.adaptive:
                print(f"🌀 Ajustando parâmetros dinâmicos ({random.randint(50,100)}%)")

    def stop(self):
        self.running = False
