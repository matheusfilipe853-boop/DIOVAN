"""
Gerenciador de memória e contexto.
Decide se usa base local (offline) ou nuvem (online).
"""

class MemoryManager:
    def __init__(self, mode="local"):
        self.mode = mode  # "local" ou "cloud"

    def store(self, key: str, value: str):
        """Armazena informação na base de conhecimento"""
        # TODO: implementar com SQLite (local) ou API (cloud)
        pass

    def retrieve(self, query: str) -> str:
        """Busca informação relevante para o contexto"""
        # TODO: implementar busca semântica
        pass
