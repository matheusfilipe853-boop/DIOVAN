"""
Factory que detecta o SO e retorna o adaptador correto.
O resto do código nunca precisa saber qual SO está rodando.
"""

import platform
from adapters.base_adapter import BaseAdapter

class AdapterFactory:
    @staticmethod
    def get_adapter() -> BaseAdapter:
        system = platform.system()

        if system == "Linux":
            from adapters.linux.linux_adapter import LinuxAdapter
            return LinuxAdapter()
        elif system == "Windows":
            from adapters.windows.windows_adapter import WindowsAdapter
            return WindowsAdapter()
        elif system == "Darwin":
            from adapters.mac.mac_adapter import MacAdapter
            return MacAdapter()
        else:
            raise Exception(f"Sistema operacional não suportado: {system}")
