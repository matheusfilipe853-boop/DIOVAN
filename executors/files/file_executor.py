import os
from executors.base_executor import BaseExecutor

class FileExecutor(BaseExecutor):
    def execute(self, command: dict) -> dict:
        path    = command.get("params", {}).get("path", "")
        max_chars = command.get("params", {}).get("max_chars", 2000)

        if not path or not os.path.exists(path):
            return {"success": False, "output": f"Arquivo não encontrado: {path}"}

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Limita o conteúdo enviado ao modelo
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[... conteúdo truncado ...]"

        return {"success": True, "output": content}
