"""
DIOVAN — Package Structure Specification
Define a estrutura oficial de todos os tipos de pacotes .diovan
Versão: 1.0

Tipos de pacotes:
  Tipo 0 → ACAO       (2 bytes namespace)
  Tipo 1 → LINGUAGEM  (4 bytes namespace)
  Tipo 2 → CONHECIMENTO (3 bytes namespace)
  Tipo 3 → VISUALIZACAO (2 bytes namespace)
  Tipo 4 → EXECUCAO   (2 bytes namespace)
"""

import struct
import hashlib
import json
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────
# CONSTANTES DO PROTOCOLO
# ─────────────────────────────────────────

MAGIC_BYTES    = b'DIOV'           # Assinatura obrigatória
WEIGHTS        = (2, 6, 0, 6, 2, 0, 0, 6)  # Pesos 26062006

# Tipos de pacote e seus espaços de endereçamento
PACKAGE_TYPES = {
    0: {"nome": "ACAO",          "namespace_bytes": 2, "max_entries": 65_536},
    1: {"nome": "LINGUAGEM",     "namespace_bytes": 4, "max_entries": 4_294_967_296},
    2: {"nome": "CONHECIMENTO",  "namespace_bytes": 3, "max_entries": 16_777_216},
    3: {"nome": "VISUALIZACAO",  "namespace_bytes": 2, "max_entries": 65_536},
    4: {"nome": "EXECUCAO",      "namespace_bytes": 2, "max_entries": 65_536},
}

# ─────────────────────────────────────────
# WEIGHT ENGINE
# ─────────────────────────────────────────

def calculate_address(index: int, package_type: int) -> int:
    """
    Calcula endereço de uma entrada no namespace do pacote.
    Usa os pesos 26062006 aplicados ao índice.
    """
    namespace_bytes = PACKAGE_TYPES[package_type]["namespace_bytes"]
    max_val         = (2 ** (namespace_bytes * 8)) - 1

    # Aplica pesos ciclicamente sobre os bits do índice
    bits  = []
    temp  = index
    for _ in range(namespace_bytes * 8):
        bits.append(temp & 1)
        temp >>= 1
    bits.reverse()

    total = 0
    for i, bit in enumerate(bits):
        weight = WEIGHTS[i % 8]
        total += bit * weight

    # Garante que o endereço está dentro do espaço do tipo
    return total % (max_val + 1)

# ─────────────────────────────────────────
# HEADER DO PACOTE
# ─────────────────────────────────────────

class PackageHeader:
    """
    Header fixo de todo arquivo .diovan

    Estrutura:
      4 bytes → assinatura mágica DIOV
      1 byte  → tipo do pacote (0-4)
      1 byte  → versão do pacote
      4 bytes → ID único (hash)
      4 bytes → tamanho do payload
      4 bytes → timestamp de criação
    """
    SIZE = 18  # bytes fixos

    def __init__(self, package_type: int, version: int = 1):
        if package_type not in PACKAGE_TYPES:
            raise ValueError(f"Tipo inválido: {package_type}")

        self.magic        = MAGIC_BYTES
        self.package_type = package_type
        self.version      = version
        self.created_at   = int(datetime.now().timestamp())
        self.payload_size = 0
        self.package_id   = 0

    def set_payload_size(self, size: int):
        self.payload_size = size

    def generate_id(self, content: bytes):
        """Gera ID único baseado no conteúdo"""
        hash_bytes     = hashlib.md5(content).digest()[:4]
        self.package_id = struct.unpack(">I", hash_bytes)[0]

    def to_bytes(self) -> bytes:
        return (
            self.magic +
            struct.pack("B", self.package_type) +
            struct.pack("B", self.version) +
            struct.pack(">I", self.package_id) +
            struct.pack(">I", self.payload_size) +
            struct.pack(">I", self.created_at)
        )

    @classmethod
    def from_bytes(cls, data: bytes) -> "PackageHeader":
        if len(data) < cls.SIZE:
            raise ValueError("Header muito pequeno")
        if data[:4] != MAGIC_BYTES:
            raise ValueError(f"Assinatura inválida: {data[:4]}")

        header              = cls.__new__(cls)
        header.magic        = data[:4]
        header.package_type = struct.unpack("B", data[4:5])[0]
        header.version      = struct.unpack("B", data[5:6])[0]
        header.package_id   = struct.unpack(">I", data[6:10])[0]
        header.payload_size = struct.unpack(">I", data[10:14])[0]
        header.created_at   = struct.unpack(">I", data[14:18])[0]
        return header

    def __repr__(self):
        tipo = PACKAGE_TYPES.get(self.package_type, {}).get("nome", "UNKNOWN")
        return (
            f"PackageHeader("
            f"tipo={tipo}, "
            f"versao={self.version}, "
            f"id={self.package_id}, "
            f"payload={self.payload_size}b)"
        )

# ─────────────────────────────────────────
# MANIFEST DO PACOTE
# ─────────────────────────────────────────

class PackageManifest:
    """
    Manifest com metadados do pacote.
    Armazenado como JSON dentro do payload.
    """

    def __init__(self, name: str, author: str,
                 package_type: int, version: str = "1.0.0"):
        self.name         = name
        self.author       = author
        self.package_type = package_type
        self.version      = version
        self.created_at   = datetime.now().isoformat()
        self.dependencies = []
        self.namespace    = {}

    def reserve_namespace(self, prefix: int, size: int):
        """Reserva um intervalo de endereços para este pacote"""
        self.namespace = {
            "prefix" : prefix,
            "size"   : size,
            "start"  : prefix,
            "end"    : prefix + size - 1
        }

    def to_dict(self) -> dict:
        return {
            "name"        : self.name,
            "author"      : self.author,
            "type"        : self.package_type,
            "type_name"   : PACKAGE_TYPES[self.package_type]["nome"],
            "version"     : self.version,
            "created_at"  : self.created_at,
            "dependencies": self.dependencies,
            "namespace"   : self.namespace,
        }

    def to_bytes(self) -> bytes:
        return json.dumps(self.to_dict(), ensure_ascii=False).encode("utf-8")

# ─────────────────────────────────────────
# LOOKUP TABLE DO PACOTE
# ─────────────────────────────────────────

class PackageLookup:
    """
    Tabela de entradas do pacote.
    Cada entrada tem: endereço, nome, dados.
    """

    def __init__(self, package_type: int):
        self.package_type = package_type
        self.entries      = {}  # endereço → entrada
        self.index        = 0   # contador de entradas

    def add(self, name: str, data: dict) -> int:
        """Adiciona entrada e retorna o endereço calculado"""
        self.index   += 1
        address       = calculate_address(self.index, self.package_type)

        # Garante unicidade de endereço
        while address in self.entries:
            self.index += 1
            address     = calculate_address(self.index, self.package_type)

        self.entries[address] = {
            "name"   : name,
            "index"  : self.index,
            "data"   : data,
        }
        return address

    def get(self, address: int) -> dict:
        return self.entries.get(address)

    def find_by_name(self, name: str) -> tuple:
        """Retorna (endereço, entrada) pelo nome"""
        for addr, entry in self.entries.items():
            if entry["name"] == name:
                return addr, entry
        return None, None

    def to_bytes(self) -> bytes:
        return json.dumps(
            {str(k): v for k, v in self.entries.items()},
            ensure_ascii=False
        ).encode("utf-8")

    def __len__(self):
        return len(self.entries)

# ─────────────────────────────────────────
# PACOTE COMPLETO
# ─────────────────────────────────────────

class DiovanPackage:
    """
    Pacote .diovan completo.
    Combina header + manifest + lookup + checksum.
    """

    def __init__(self, name: str, author: str, package_type: int):
        self.header   = PackageHeader(package_type)
        self.manifest = PackageManifest(name, author, package_type)
        self.lookup   = PackageLookup(package_type)

    def add_entry(self, name: str, data: dict) -> int:
        """Adiciona entrada ao pacote e retorna o endereço"""
        return self.lookup.add(name, data)

    def save(self, path: Path):
        """Serializa e salva o pacote em disco"""

        # Monta payload
        manifest_bytes = self.manifest.to_bytes()
        lookup_bytes   = self.lookup.to_bytes()

        # Separador entre manifest e lookup
        separator = b'\x00\xFF\x00\xFF'

        payload = manifest_bytes + separator + lookup_bytes

        # Calcula checksum
        checksum = hashlib.sha256(payload).digest()[:4]

        # Finaliza header
        self.header.set_payload_size(len(payload))
        self.header.generate_id(payload)

        # Escreve arquivo
        with open(path, "wb") as f:
            f.write(self.header.to_bytes())
            f.write(payload)
            f.write(checksum)

        return path

    @classmethod
    def load(cls, path: Path) -> "DiovanPackage":
        """Carrega e valida um pacote .diovan"""
        with open(path, "rb") as f:
            data = f.read()

        # Valida header
        header = PackageHeader.from_bytes(data[:PackageHeader.SIZE])

        # Extrai payload e checksum
        payload_start = PackageHeader.SIZE
        payload_end   = payload_start + header.payload_size
        payload       = data[payload_start:payload_end]
        checksum      = data[payload_end:payload_end + 4]

        # Valida checksum
        expected = hashlib.sha256(payload).digest()[:4]
        if checksum != expected:
            raise ValueError("Checksum inválido — pacote corrompido ou adulterado")

        # Parseia payload
        separator = b'\x00\xFF\x00\xFF'
        sep_idx   = payload.find(separator)

        manifest_bytes = payload[:sep_idx]
        lookup_bytes   = payload[sep_idx + 4:]

        manifest_dict = json.loads(manifest_bytes.decode("utf-8"))
        lookup_dict   = json.loads(lookup_bytes.decode("utf-8"))

        # Reconstrói objeto
        pkg          = cls.__new__(cls)
        pkg.header   = header
        pkg.manifest = PackageManifest(
            manifest_dict["name"],
            manifest_dict["author"],
            manifest_dict["type"]
        )
        pkg.lookup         = PackageLookup(header.package_type)
        pkg.lookup.entries = {int(k): v for k, v in lookup_dict.items()}

        return pkg

    def __repr__(self):
        tipo = PACKAGE_TYPES[self.header.package_type]["nome"]
        return (
            f"DiovanPackage("
            f"nome={self.manifest.name}, "
            f"tipo={tipo}, "
            f"entradas={len(self.lookup)})"
        )

# ─────────────────────────────────────────
# TESTE
# ─────────────────────────────────────────

if __name__ == "__main__":
    print("DIOVAN Package Spec — Teste\n")
    print("=" * 50)

    # Mostra espaços de endereçamento por tipo
    print("\nTipos de pacote disponíveis:")
    for tipo_id, info in PACKAGE_TYPES.items():
        print(f"  Tipo {tipo_id} — {info['nome']}")
        print(f"    Namespace: {info['namespace_bytes']} bytes")
        print(f"    Endereços: {info['max_entries']:,}")

    # Cria pacote de linguagem de exemplo
    print("\n\nCriando language.diovan...")
    pkg = DiovanPackage(
        name         = "language",
        author       = "Matheus F. Souza",
        package_type = 1  # LINGUAGEM
    )

    # Adiciona conceitos de exemplo
    conceitos = [
        ("AFIRMACAO", {"palavras": ["sim", "ok", "certo", "claro", "exato"]}),
        ("NEGACAO",   {"palavras": ["não", "nunca", "jamais", "nenhum"]}),
        ("ACAO",      {"palavras": ["fazer", "executar", "criar", "gerar"]}),
        ("TEMPO",     {"palavras": ["agora", "hoje", "amanhã", "quando"]}),
        ("IDENTIDADE",{"palavras": ["diovan", "projeto", "sistema", "eu"]}),
    ]

    print("\nEndereços gerados:")
    for nome, data in conceitos:
        addr = pkg.add_entry(nome, data)
        print(f"  {nome} → endereço {addr}")

    # Salva
    output = Path("./knowledge/language.diovan")
    output.parent.mkdir(parents=True, exist_ok=True)
    pkg.save(output)
    print(f"\nSalvo em: {output}")
    print(f"Tamanho: {output.stat().st_size} bytes")

    # Recarrega e valida
    print("\nValidando leitura...")
    pkg2 = DiovanPackage.load(output)
    print(f"Pacote carregado: {pkg2}")
    print(f"Checksum: OK")

    # Testa busca por nome
    addr, entry = pkg2.lookup.find_by_name("AFIRMACAO")
    print(f"\nBusca AFIRMACAO → endereço {addr}")
    print(f"Palavras: {entry['data']['palavras']}")

    print("\nPackage Spec validado com sucesso!")
