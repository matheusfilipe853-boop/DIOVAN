"""
DIOVAN — Ponto de entrada
Detecta o terminal correto e inicia a interface
"""

import os
import sys
import subprocess

def launch_external_terminal():
    """Abre um terminal externo dedicado ao DIOVAN"""
    script_path = os.path.abspath(__file__)
    project_dir = os.path.dirname(script_path)

    # Comando para rodar o DIOVAN dentro do terminal externo
    run_cmd = f"cd {project_dir} && source venv/bin/activate && python3 diovan.py; exec bash"

    # Tenta abrir no terminal disponível no sistema
    terminals = [
        ["gnome-terminal", "--title=DIOVAN", "--", "bash", "-c", run_cmd],
        ["xterm", "-title", "DIOVAN", "-e", f"bash -c '{run_cmd}'"],
        ["konsole", "--title", "DIOVAN", "-e", f"bash -c '{run_cmd}'"],
        ["xfce4-terminal", "--title=DIOVAN", "-e", f"bash -c '{run_cmd}'"],
    ]

    for terminal_cmd in terminals:
        try:
            subprocess.Popen(terminal_cmd)
            print(f"✅ DIOVAN iniciado em terminal externo: {terminal_cmd[0]}")
            return True
        except FileNotFoundError:
            continue

    # Fallback: roda no terminal atual
    print("⚠️  Nenhum terminal externo encontrado. Rodando no terminal atual.")
    return False

if __name__ == "__main__":
    # Se já está dentro do terminal externo (chamado por diovan.py), não relança
    if "--embedded" in sys.argv:
        from diovan import run
        run()
    else:
        launched = launch_external_terminal()
        if not launched:
            from diovan import run
            run()
