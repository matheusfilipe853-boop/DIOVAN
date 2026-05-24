"""
DIOVAN — Weight Engine
Carrega os pesos do .env.weights e calcula valores de instruções.
O núcleo nunca conhece os pesos diretamente.
O núcleo consulta este módulo que lê do arquivo externo.

CRÍTICO:
- Os pesos são carregados UMA VEZ na inicialização
- O arquivo .env.weights nunca é relido durante execução
- Se .env.weights não existir, o DIOVAN não inicializa
"""

import os
from pathlib import Path
from dotenv import dotenv_values

# Caminho do arquivo de pesos — nunca no .env principal
WEIGHTS_FILE = Path(".env.weights")

class WeightEngine:
    """
    Motor de pesos do protocolo DIOVAN.
    Carrega os pesos uma vez e os mantém em memória.
    """

    def __init__(self):
        self._weights = None
        self._version = None
        self._locked  = False
        self._load()

    def _load(self):
        """Carrega pesos do arquivo externo. Falha se não encontrar."""
        if not WEIGHTS_FILE.exists():
            raise FileNotFoundError(
                f"CRÍTICO: {WEIGHTS_FILE} não encontrado. "
                "O DIOVAN não pode inicializar sem os pesos. "
                "Restaure o backup."
            )

        config = dotenv_values(WEIGHTS_FILE)

        # Valida que todos os pesos estão presentes
        required = [f"DIOVAN_W{i}" for i in range(1, 9)]
        missing  = [k for k in required if k not in config]

        if missing:
            raise ValueError(
                f"CRÍTICO: Pesos ausentes em {WEIGHTS_FILE}: {missing}"
            )

        # Carrega em memória — arquivo nunca mais consultado
        self._weights = tuple(int(config[f"DIOVAN_W{i}"]) for i in range(1, 9))
        self._version = int(config.get("DIOVAN_WEIGHTS_VERSION", 1))
        self._locked  = config.get("DIOVAN_WEIGHTS_LOCKED", "false").lower() == "true"

        # Valida que pesos são derivados do sistema trinário 2,6,0
        valid_symbols = {0, 2, 6}
        invalid = [w for w in self._weights if w not in valid_symbols]
        if invalid:
            raise ValueError(
                f"CRÍTICO: Pesos inválidos {invalid}. "
                "Apenas os símbolos 0, 2, 6 são permitidos."
            )

    def calculate(self, instruction: bytes) -> int:
        """
        Calcula o valor de uma instrução de 8 bytes
        aplicando o sistema posicional com pesos 26062006.

        Cada bit da instrução é multiplicado pelo peso da sua posição.
        Retorna o valor inteiro resultante.
        """
        if len(instruction) != 8:
            raise ValueError(f"Instrução deve ter 8 bytes. Recebido: {len(instruction)}")

        total = 0
        for byte_idx, byte_val in enumerate(instruction):
            weight = self._weights[byte_idx]
            # Cada bit do byte multiplicado pelo peso da posição
            for bit_idx in range(8):
                bit = (byte_val >> (7 - bit_idx)) & 1
                total += bit * weight

        return total

    def calculate_field(self, byte_val: int, position: int) -> int:
        """
        Calcula o valor de um único byte em uma posição específica.
        Usado para calcular campos individuais da instrução.

        position: 0-7 (posição na instrução)
        """
        if position < 0 or position > 7:
            raise ValueError(f"Posição inválida: {position}. Deve ser 0-7.")

        weight = self._weights[position]
        total  = 0

        for bit_idx in range(8):
            bit    = (byte_val >> (7 - bit_idx)) & 1
            total += bit * weight

        return total

    def verify_compatibility(self, other_weights: tuple) -> bool:
        """
        Verifica se outro conjunto de pesos é compatível com este.
        Retorna True apenas se forem idênticos.
        Usado para detectar instâncias incompatíveis (réplicas).
        """
        return self._weights == other_weights

    @property
    def weights(self) -> tuple:
        return self._weights

    @property
    def version(self) -> int:
        return self._version

    @property
    def is_locked(self) -> bool:
        return self._locked

    def __repr__(self):
        # Nunca expõe os pesos no repr
        return f"WeightEngine(version={self._version}, locked={self._locked})"


# ─────────────────────────────────────────
# VALIDAÇÃO
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("Testando WeightEngine...\n")

    engine = WeightEngine()
    print(f"Engine: {engine}")
    print(f"Versão: {engine.version}")
    print(f"Bloqueado: {engine.is_locked}\n")

    # Testa instrução conhecida
    # INTENT=QUERY (00000001) na posição 0 com peso 2
    # valor esperado: apenas o último bit ativo × peso 2 = 2
    test_instruction = bytes([
        0b00000001,  # Posição 0: peso 2 → valor 2
        0b00000000,  # Posição 1: peso 6 → valor 0
        0b00000000,  # Posição 2: peso 0 → valor 0 (zona de silêncio)
        0b00000000,  # Posição 3: peso 6 → valor 0
        0b00000000,  # Posição 4: peso 2 → valor 0
        0b00000000,  # Posição 5: peso 0 → valor 0 (zona de silêncio)
        0b00000000,  # Posição 6: peso 0 → valor 0 (zona de silêncio)
        0b00000000,  # Posição 7: peso 6 → valor 0
    ])

    valor = engine.calculate(test_instruction)
    print(f"Instrução: {test_instruction.hex()}")
    print(f"Valor calculado: {valor}")
    print(f"Esperado: 2 (bit 1 na posição 0 com peso 2)")
    print(f"Correto: {valor == 2}\n")

    # Testa campo individual
    campo_intent = engine.calculate_field(0b00000001, position=0)
    print(f"Campo INTENT (00000001 na posição 0): {campo_intent}")
    print(f"Esperado: 2")
    print(f"Correto: {campo_intent == 2}\n")

    # Demonstra zonas de silêncio
    print("Zonas de silêncio (posições com peso 0):")
    for i, w in enumerate(engine.weights):
        if w == 0:
            print(f"  Posição {i+1}: peso {w} → SILÊNCIO")

    print("\nWeightEngine validado com sucesso.")
