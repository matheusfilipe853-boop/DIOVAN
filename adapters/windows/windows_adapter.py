"""
Adaptador Windows.
TODO: implementar quando necessário.
"""

from adapters.base_adapter import BaseAdapter

class WindowsAdapter(BaseAdapter):
    def run(self, action: str, params: dict) -> dict:
        # TODO: implementar com subprocess e powershell
        return {"success": False, "output": "Windows adapter não implementado ainda"}

    def get_system_info(self) -> dict:
        return {"os": "Windows"}
