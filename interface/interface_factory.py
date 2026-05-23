"""
DIOVAN — Interface Factory
Detecta e carrega o adapter de interface correto via .env
"""

import os
from dotenv import load_dotenv

load_dotenv()

class InterfaceFactory:
    @staticmethod
    def get_interface():
        adapter = os.getenv("DIOVAN_INTERFACE", "terminal")

        if adapter == "terminal":
            from interface.adapters.terminal import TerminalAdapter
            return TerminalAdapter()

        # Futuro
        # elif adapter == "electron":
        #     from interface.adapters.electron import ElectronAdapter
        #     return ElectronAdapter()
        # elif adapter == "web":
        #     from interface.adapters.web import WebAdapter
        #     return WebAdapter()

        raise Exception(f"Interface não suportada: {adapter}")
