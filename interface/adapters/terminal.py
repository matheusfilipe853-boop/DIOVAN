"""
DIOVAN — Terminal Adapter
Abre um terminal externo dedicado com identidade visual própria.
Primeiro adapter de interface do DIOVAN.
"""

import os
import sys
import subprocess
from interface.base_interface import BaseInterface

# Cores ANSI
class Colors:
    RESET   = "\033[0m"
    BOLD    = "\033[1m"
    CYAN    = "\033[96m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    RED     = "\033[91m"
    WHITE   = "\033[97m"
    DIM     = "\033[2m"
    BLUE    = "\033[94m"

BANNER = f"""
{Colors.CYAN}{Colors.BOLD}
██████╗ ██╗ ██████╗ ██╗   ██╗ █████╗ ███╗   ██╗
██╔══██╗██║██╔═══██╗██║   ██║██╔══██╗████╗  ██║
██║  ██║██║██║   ██║██║   ██║███████║██╔██╗ ██║
██║  ██║██║██║   ██║╚██╗ ██╔╝██╔══██║██║╚██╗██║
██████╔╝██║╚██████╔╝ ╚████╔╝ ██║  ██║██║ ╚████║
╚═════╝ ╚═╝ ╚═════╝   ╚═══╝  ╚═╝  ╚═╝╚═╝  ╚═══╝
{Colors.RESET}{Colors.DIM}Domine · Intelligent · Omni · Vitae · Agent · Neural{Colors.RESET}
{Colors.DIM}O senhor da inteligência neural onipresente viva{Colors.RESET}
"""

SEPARATOR = f"{Colors.DIM}{'─' * 60}{Colors.RESET}"

class TerminalAdapter(BaseInterface):

    def start(self, on_input, on_exit):
        """Inicia o loop de conversa no terminal"""
        self._print_banner()

        while True:
            try:
                user_input = input(
                    f"\n{Colors.CYAN}{Colors.BOLD}▸ Você:{Colors.RESET} "
                ).strip()

                if not user_input:
                    continue

                if user_input.lower() in ["sair", "exit", "quit", ":q"]:
                    self._print_exit()
                    on_exit()
                    break

                on_input(user_input)

            except KeyboardInterrupt:
                self._print_exit()
                on_exit()
                break
            except EOFError:
                break

    def render_response(self, text: str):
        print(f"\n{Colors.GREEN}{Colors.BOLD}> DIOVAN:{Colors.RESET}")
        print(f"{Colors.WHITE}{text}{Colors.RESET}")
        print(SEPARATOR)

    def render_status(self, text: str):
        print(f"\n{Colors.YELLOW}> {text}{Colors.RESET}", end="", flush=True)

    def render_error(self, text: str):
        print(f"\n{Colors.RED}! {text}{Colors.RESET}")

    def _print_banner(self):
        os.system("clear")
        print(BANNER)
        print(SEPARATOR)
        print(f"{Colors.DIM}  Digite 'sair' para encerrar · Ctrl+C para interromper{Colors.RESET}")
        print(SEPARATOR)

    def _print_exit(self):
        print(f"\n{Colors.CYAN}◈ DIOVAN encerrado. Até logo, Matheus.{Colors.RESET}\n")
