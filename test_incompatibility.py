"""
DIOVAN — Teste de Incompatibilidade por Natureza
Prova que sem os pesos corretos o pacote é ilegível.

Fluxo:
1. Lê language.diovan original
2. Cria clone com pesos alterados
3. Tenta ler o clone com pesos errados
4. Compara resultados
5. Apaga o clone
6. Devolve resumo
"""

import os
import sys
import shutil
import hashlib
import json
import struct
from pathlib import Path
from dotenv import dotenv_values

sys.path.insert(0, str(Path(__file__).parent))
from core.diovan_package_spec import DiovanPackage, PackageHeader, PackageLookup

# ─────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────

ORIGINAL_PATH = Path("./knowledge/language.diovan")
CLONE_PATH    = Path("/tmp/language_clone.diovan")
WEIGHTS_FILE  = Path(".env.weights")

# ─────────────────────────────────────────
# WEIGHT ENGINE COM PESOS CUSTOMIZADOS
# ─────────────────────────────────────────

def calculate_address_with_weights(index: int, weights: tuple) -> int:
    """Calcula endereço com pesos específicos"""
    bits  = [(index >> (7 - i)) & 1 for i in range(8)]
    return sum(bit * weights[i % 8] for i, bit in enumerate(bits))

def load_real_weights() -> tuple:
    """Carrega os pesos reais do .env.weights"""
    config = dotenv_values(WEIGHTS_FILE)
    return tuple(int(config[f"DIOVAN_W{i}"]) for i in range(1, 9))

# ─────────────────────────────────────────
# CLONE COM PESOS ALTERADOS
# ─────────────────────────────────────────

def create_corrupted_clone(original: Path, clone: Path, fake_weights: tuple):
    """
    Cria uma cópia do pacote recalculando os endereços
    com pesos diferentes dos originais.
    """
    with open(original, "rb") as f:
        data = f.read()

    # Lê header original
    header = PackageHeader.from_bytes(data[:PackageHeader.SIZE])

    # Extrai payload
    payload_start = PackageHeader.SIZE
    payload_end   = payload_start + header.payload_size
    payload       = data[payload_start:payload_end]

    # Parseia lookup original
    separator  = b'\x00\xFF\x00\xFF'
    sep_idx    = payload.find(separator)
    manifest_bytes = payload[:sep_idx]
    lookup_bytes   = payload[sep_idx + 4:]

    lookup_dict = json.loads(lookup_bytes.decode("utf-8"))

    # Recalcula endereços com pesos falsos
    corrupted_lookup = {}
    for idx, (_, entry) in enumerate(lookup_dict.items()):
        fake_addr = calculate_address_with_weights(idx + 1, fake_weights)
        # Garante unicidade mesmo com pesos errados
        while fake_addr in corrupted_lookup:
            idx += 1
            fake_addr = calculate_address_with_weights(idx + 1, fake_weights)
        corrupted_lookup[fake_addr] = entry

    # Remonta payload com lookup corrompida
    corrupted_lookup_bytes = json.dumps(
        {str(k): v for k, v in corrupted_lookup.items()},
        ensure_ascii=False
    ).encode("utf-8")

    new_payload  = manifest_bytes + separator + corrupted_lookup_bytes
    new_checksum = hashlib.sha256(new_payload).digest()[:4]

    # Salva clone
    header.set_payload_size(len(new_payload))
    header.generate_id(new_payload)

    with open(clone, "wb") as f:
        f.write(header.to_bytes())
        f.write(new_payload)
        f.write(new_checksum)

    return corrupted_lookup

# ─────────────────────────────────────────
# COMPARADOR DE RESULTADOS
# ─────────────────────────────────────────

def compare_lookups(original_pkg: DiovanPackage,
                    fake_weights: tuple,
                    corrupted_lookup: dict) -> dict:
    """Compara endereços originais vs corrompidos"""

    real_weights = load_real_weights()
    results      = []
    mismatches   = 0

    # Pega as primeiras 5 entradas para comparar
    for addr, entry in list(original_pkg.lookup.entries.items())[:5]:
        nome      = entry["name"]
        palavras  = entry["data"].get("palavras", [])[:2]

        # Endereço com pesos reais
        real_addr = addr

        # Endereço com pesos falsos
        idx       = entry["index"]
        fake_addr = calculate_address_with_weights(idx, fake_weights)

        match = real_addr == fake_addr
        if not match:
            mismatches += 1

        results.append({
            "conceito"  : nome,
            "palavras"  : palavras,
            "addr_real" : real_addr,
            "addr_fake" : fake_addr,
            "match"     : match
        })

    return {
        "total"     : len(results),
        "mismatches": mismatches,
        "entries"   : results
    }

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def run():
    print("DIOVAN — Teste de Incompatibilidade por Natureza")
    print("=" * 55)

    # 1. Verifica pacote original
    print("\n1. Carregando pacote original...")
    if not ORIGINAL_PATH.exists():
        print(f"Pacote nao encontrado: {ORIGINAL_PATH}")
        sys.exit(1)

    original_pkg = DiovanPackage.load(ORIGINAL_PATH)
    real_weights = load_real_weights()
    print(f"   {original_pkg}")
    print(f"   Pesos reais carregados: {real_weights}")

    # 2. Define pesos falsos (sem a chave 26062006)
    fake_weights = (1, 2, 3, 4, 5, 6, 7, 8)  # pesos genéricos
    print(f"\n2. Pesos falsos (sem chave): {fake_weights}")

    # 3. Cria clone corrompido
    print("\n3. Criando clone com pesos alterados...")
    corrupted = create_corrupted_clone(ORIGINAL_PATH, CLONE_PATH, fake_weights)
    print(f"   Clone criado em: {CLONE_PATH}")
    print(f"   {len(corrupted)} entradas recalculadas com pesos errados")

    # 4. Compara resultados
    print("\n4. Comparando enderecos originais vs corrompidos:")
    print(f"   {'Conceito':<22} {'Addr Real':>10} {'Addr Falso':>10} {'Match':>6}")
    print(f"   {'-'*52}")

    comparison = compare_lookups(original_pkg, fake_weights, corrupted)
    for entry in comparison["entries"]:
        match_str = "OK" if entry["match"] else "DIFERENTE"
        print(
            f"   {entry['conceito']:<22} "
            f"{entry['addr_real']:>10} "
            f"{entry['addr_fake']:>10} "
            f"{match_str:>9}"
        )

    # 5. Tenta buscar conceito no clone
    print("\n5. Tentando buscar AFIRMACAO no clone...")
    clone_pkg          = DiovanPackage.load(CLONE_PATH)
    addr_real, _       = original_pkg.lookup.find_by_name("AFIRMACAO")
    addr_clone, entry  = clone_pkg.lookup.find_by_name("AFIRMACAO")

    if addr_real != addr_clone:
        print(f"   AFIRMACAO no original → endereço {addr_real}")
        print(f"   AFIRMACAO no clone    → endereço {addr_clone}")
        print(f"   Enderecos DIFERENTES — pacote incompativel por natureza")
    else:
        print(f"   Enderecos iguais (pesos coincidiram neste caso)")

    # 6. Apaga clone
    print("\n6. Apagando clone...")
    CLONE_PATH.unlink()
    print(f"   Clone removido: {CLONE_PATH}")

    # 7. Resumo
    print("\n" + "=" * 55)
    print("RESUMO DO TESTE")
    print("=" * 55)
    print(f"Entradas testadas : {comparison['total']}")
    print(f"Incompatibilidades: {comparison['mismatches']}/{comparison['total']}")

    if comparison["mismatches"] > 0:
        pct = (comparison["mismatches"] / comparison["total"]) * 100
        print(f"Taxa de erro      : {pct:.0f}%")
        print(f"\nCONCLUSAO: Sem os pesos 26062006, o pacote e")
        print(f"matematicamente incompativel.")
        print(f"Os enderecos sao diferentes por natureza.")
        print(f"Nenhuma regra de software necessaria.")
        print(f"A matematica protege.")
    else:
        print(f"\nATENCAO: Pesos falsos coincidiram neste caso.")
        print(f"Tente pesos mais distantes dos originais.")

if __name__ == "__main__":
    run()
