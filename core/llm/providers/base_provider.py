"""
Classe base para todos os provedores de LLM.
Qualquer novo provedor (Ollama, Claude, GPT) herda daqui.
Garante que a interface seja sempre a mesma.
"""

from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    def send(self, prompt: str) -> str:
        """Envia prompt e retorna resposta como string"""
        pass
