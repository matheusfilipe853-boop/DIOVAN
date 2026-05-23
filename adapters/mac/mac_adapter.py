"""
Adaptador macOS.
TODO: implementar quando necessário.
"""

from adapters.base_adapter import BaseAdapter

class MacAdapter(BaseAdapter):
    def run(self, action: str, params: dict) -> dict:
        # TODO: implementar
        return {"success": False, "output": "Mac adapter não implementado ainda"}

    def get_system_info(self) -> dict:
        return {"os": "macOS"}
