"""
DIOVAN — Interface LLM
Suporta múltiplos modelos via parâmetro.
Permite roteamento por complexidade no orquestrador.
"""

import os
from dotenv import load_dotenv
from core.llm.providers.ollama_provider import OllamaProvider

load_dotenv()

class LLMInterface:
    def __init__(self, model: str = None):
        # Se modelo não especificado, usa o do .env
        self.model    = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.provider = OllamaProvider(model=self.model)

    def process(self, text: str, history: list = []) -> str:
        return self.provider.send(text, history)
