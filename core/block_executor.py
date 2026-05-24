"""
DIOVAN — Block Executor
Executa blocos de instruções em sequência.
Passa contexto entre instruções automaticamente.
Gerencia confirmações para ações de risco alto.
"""

import os
from typing import Callable, Optional
from core.nucleus import get_nucleus, RISK

# ─────────────────────────────────────────
# INSTRUÇÃO
# ─────────────────────────────────────────

class Instruction:
    """
    Instrução atômica do protocolo DIOVAN.
    Representa uma ação a ser executada.
    """
    def __init__(self, skill: str, params: dict = None,
                 risk: str = "LOW", description: str = ""):
        self.skill       = skill
        self.params      = params or {}
        self.risk        = risk
        self.description = description

    def __repr__(self):
        return f"Instruction({self.skill}, risk={self.risk})"

# ─────────────────────────────────────────
# BLOCO DE EXECUÇÃO
# ─────────────────────────────────────────

class ExecutionBlock:
    """
    Bloco com N instruções encadeadas.
    Executa em sequência, passando contexto entre elas.
    """
    def __init__(self, mission: str):
        self.mission      = mission
        self.instructions = []

    def add(self, instruction: Instruction):
        self.instructions.append(instruction)
        return self

    def __repr__(self):
        return (
            f"ExecutionBlock("
            f"missao='{self.mission}', "
            f"instrucoes={len(self.instructions)})"
        )

# ─────────────────────────────────────────
# EXECUTOR
# ─────────────────────────────────────────

class BlockExecutor:
    """
    Executa blocos de instrução do DIOVAN.
    Gerencia contexto, confirmações e resultados.
    """

    def __init__(self, on_confirm: Callable = None,
                       on_status:  Callable = None):
        self.nucleus    = get_nucleus()
        self.on_confirm = on_confirm or self._default_confirm
        self.on_status  = on_status  or self._default_status

    def execute(self, block: ExecutionBlock) -> dict:
        """
        Executa todas as instruções do bloco em sequência.
        Retorna o contexto final com todos os resultados.
        """
        context = {
            "mission" : block.mission,
            "results" : [],
            "success" : True,
            "error"   : None,
        }

        self.on_status(f"Iniciando missão: {block.mission}")
        self.on_status(f"{len(block.instructions)} instrução(ões) no bloco")

        for i, instruction in enumerate(block.instructions):
            self.on_status(
                f"[{i+1}/{len(block.instructions)}] "
                f"{instruction.skill}"
            )

            # Verifica risco e solicita confirmação se necessário
            if not self._check_risk(instruction):
                context["success"] = False
                context["error"]   = f"Instrução cancelada: {instruction.skill}"
                self.on_status(f"Cancelado pelo usuário: {instruction.skill}")
                break

            # Resolve o pacote que tem essa skill
            pkg_name, package = self.nucleus.resolve_skill(instruction.skill)
            if not package:
                context["success"] = False
                context["error"]   = f"Skill não encontrada: {instruction.skill}"
                self.on_status(f"Skill não disponível: {instruction.skill}")
                break

            # Prepara contexto para a instrução
            exec_context = {
                **context,
                **instruction.params,
            }

            # Executa a skill
            try:
                skill  = package.get_skill(instruction.skill)
                result = skill.execute(exec_context)

                # Adiciona resultado ao contexto
                context[instruction.skill] = result
                context["results"].append({
                    "skill"  : instruction.skill,
                    "success": result.get("success", True),
                    "data"   : result,
                })

                self.on_status(
                    f"Concluído: {instruction.skill} "
                    f"({'OK' if result.get('success', True) else 'ERRO'})"
                )

                # Se falhou, para o bloco
                if not result.get("success", True):
                    context["success"] = False
                    context["error"]   = result.get("error", "Erro desconhecido")
                    break

            except Exception as e:
                context["success"] = False
                context["error"]   = str(e)
                self.on_status(f"Erro em {instruction.skill}: {e}")
                break

        return context

    def _check_risk(self, instruction: Instruction) -> bool:
        """Verifica risco e solicita confirmação se necessário"""
        risk_level = RISK.get(instruction.risk, 1)

        if risk_level == RISK["BLOCKED"]:
            self.on_status(f"BLOQUEADO: {instruction.skill}")
            return False

        if risk_level >= RISK["HIGH"]:
            desc = instruction.description or instruction.skill
            return self.on_confirm(
                f"Confirma execução de '{desc}'? (alto risco)"
            )

        return True

    def _default_confirm(self, message: str) -> bool:
        """Confirmação padrão via terminal"""
        response = input(f"\n> {message} [s/N]: ").strip().lower()
        return response in ["s", "sim", "yes", "y"]

    def _default_status(self, message: str):
        """Status padrão via terminal"""
        print(f"  ⟳ {message}")


# ─────────────────────────────────────────
# TESTE
# ─────────────────────────────────────────

if __name__ == "__main__":
    from core.package_loader import PackageLoader, Package, Skill

    print("Testando Block Executor\n")

    nucleus = get_nucleus()
    loader  = PackageLoader(nucleus)

    # Cria pacote de teste
    def hello_handler(context: dict) -> dict:
        nome = context.get("nome", "Matheus")
        return {"success": True, "mensagem": f"Olá {nome}, DIOVAN operacional!"}

    def echo_handler(context: dict) -> dict:
        msg = context.get("HELLO_WORLD", {}).get("mensagem", "")
        return {"success": True, "echo": f"Recebido: {msg}"}

    pkg = Package("test", 0, "1.0", "DIOVAN")
    pkg.register_skill(Skill("HELLO_WORLD", hello_handler))
    pkg.register_skill(Skill("ECHO_RESULT", echo_handler))
    loader.load_python_package(pkg)

    print(f"Núcleo: {nucleus}")
    print(f"Skills: {nucleus.get_available_skills()}\n")

    # Monta bloco de execução
    block = ExecutionBlock("Teste de orquestração")
    block.add(Instruction("HELLO_WORLD", {"nome": "Matheus"}))
    block.add(Instruction("ECHO_RESULT"))

    # Executa
    executor = BlockExecutor()
    result   = executor.execute(block)

    print(f"\nResultado final:")
    print(f"  Sucesso: {result['success']}")
    for r in result["results"]:
        print(f"  {r['skill']}: {r['data']}")
