"""
Classe base para todos os executores.
Garante interface padronizada independente do que o executor faz.
"""

from abc import ABC, abstractmethod

class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, command: dict) -> dict:
        """
        Recebe um comando estruturado e retorna resultado.
        command: { "action": "...", "params": {...} }
        result:  { "success": bool, "output": "..." }
        """
        pass
