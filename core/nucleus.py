"""
DIOVAN — Nucleus
Coração do protocolo. Lookup table + roteador de pacotes.
Este arquivo nunca muda. Só cresce via pacotes externos.

Responsabilidades:
- Manter lookup table dos INTENTs do núcleo
- Rotear instruções para o pacote correto
- Nunca executar diretamente — só delegar
"""

import os
from pathlib import Path
from dotenv import dotenv_values

# ─────────────────────────────────────────
# PESOS — carregados uma vez, nunca expostos
# ─────────────────────────────────────────

_WEIGHTS_FILE = Path(".env.weights")
_WEIGHTS      = None

def _load_weights() -> tuple:
    global _WEIGHTS
    if _WEIGHTS is not None:
        return _WEIGHTS
    if not _WEIGHTS_FILE.exists():
        raise FileNotFoundError(
            "CRÍTICO: .env.weights não encontrado. "
            "O núcleo não pode inicializar."
        )
    config   = dotenv_values(_WEIGHTS_FILE)
    _WEIGHTS = tuple(int(config[f"DIOVAN_W{i}"]) for i in range(1, 9))
    return _WEIGHTS

# ─────────────────────────────────────────
# INTENTS DO NÚCLEO — imutáveis
# ─────────────────────────────────────────

def _calculate_intent_value(index: int) -> int:
    weights = _load_weights()
    bits    = [(index >> (7 - i)) & 1 for i in range(8)]
    return sum(bit * weights[i % 8] for i, bit in enumerate(bits))

# Mapa de INTENTs — valores calculados pelos pesos 26062006
INTENT_MAP = {
    "NULL"     : 0,
    "QUERY"    : None,  # calculado na inicialização
    "EXECUTE"  : None,
    "RESPOND"  : None,
    "LEARN"    : None,
    "GENERATE" : None,
    "VALIDATE" : None,
    "ABSORB"   : None,
    "DISCARD"  : None,
}

# RISK levels — imutáveis
RISK = {
    "LOW"      : 1,
    "MEDIUM"   : 2,
    "HIGH"     : 3,
    "CRITICAL" : 4,
    "BLOCKED"  : 255,
}

# ─────────────────────────────────────────
# NUCLEUS CLASS
# ─────────────────────────────────────────

class Nucleus:
    """
    Núcleo do DIOVAN.
    Mantém lookup table de pacotes carregados.
    Roteia instruções para o pacote correto.
    """

    def __init__(self):
        self._weights        = _load_weights()
        self._packages       = {}   # nome → PackageLoader
        self._skills         = {}   # skill_name → package_name
        self._initialized    = False
        self._init()

    def _init(self):
        """Inicializa o núcleo calculando os valores dos INTENTs"""
        for i, intent in enumerate(INTENT_MAP.keys()):
            if intent == "NULL":
                INTENT_MAP[intent] = 0
            else:
                INTENT_MAP[intent] = _calculate_intent_value(i)

        self._initialized = True

    def register_package(self, name: str, package):
        """Registra um pacote carregado na lookup table"""
        self._packages[name] = package

        # Registra as skills do pacote
        for skill in package.skills:
            self._skills[skill] = name

    def resolve_skill(self, skill_name: str):
        """Retorna o pacote que tem a skill solicitada"""
        package_name = self._skills.get(skill_name)
        if not package_name:
            return None, None
        return package_name, self._packages.get(package_name)

    def get_loaded_packages(self) -> list:
        return list(self._packages.keys())

    def get_available_skills(self) -> list:
        return list(self._skills.keys())

    def is_ready(self) -> bool:
        return self._initialized

    def __repr__(self):
        return (
            f"Nucleus("
            f"pacotes={len(self._packages)}, "
            f"skills={len(self._skills)})"
        )


# Instância global do núcleo — singleton
_nucleus = None

def get_nucleus() -> Nucleus:
    global _nucleus
    if _nucleus is None:
        _nucleus = Nucleus()
    return _nucleus
