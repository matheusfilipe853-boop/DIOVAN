"""
Executor de comandos do sistema operacional.
Usa adaptadores para funcionar em Linux, Windows, Mac.
"""

from executors.base_executor import BaseExecutor
from adapters.adapter_factory import AdapterFactory

class SystemExecutor(BaseExecutor):
    def __init__(self):
        self.adapter = AdapterFactory.get_adapter()

    def execute(self, command: dict) -> dict:
        action = command.get("action")
        params = command.get("params", {})

        return self.adapter.run(action, params)
