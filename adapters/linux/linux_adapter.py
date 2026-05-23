"""
Adaptador Linux.
Implementa ações específicas do Linux/Ubuntu.
"""

import subprocess
from adapters.base_adapter import BaseAdapter

class LinuxAdapter(BaseAdapter):
    def run(self, action: str, params: dict) -> dict:
        if action == "shell":
            cmd = params.get("command", "")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {"success": result.returncode == 0, "output": result.stdout or result.stderr}

        return {"success": False, "output": f"Ação não implementada: {action}"}

    def get_system_info(self) -> dict:
        result = subprocess.run("uname -a", shell=True, capture_output=True, text=True)
        return {"os": "Linux", "info": result.stdout.strip()}
