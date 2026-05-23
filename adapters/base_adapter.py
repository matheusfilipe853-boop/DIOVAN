"""
Adaptador base abstrato.
Define contrato que todo SO precisa implementar.
Permite trocar Linux por Windows sem refatorar o resto.
"""

from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    def run(self, action: str, params: dict) -> dict:
        pass

    @abstractmethod
    def get_system_info(self) -> dict:
        pass
