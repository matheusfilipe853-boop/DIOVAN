"""
DIOVAN — Package Loader
Carrega arquivos .diovan, valida integridade,
resolve dependências e registra no núcleo.
"""

import json
import hashlib
import struct
from pathlib import Path
from typing import Optional

MAGIC_BYTES   = b'DIOV'
PACKAGES_DIR  = Path("./packages")

# ─────────────────────────────────────────
# SKILL — contrato de um pacote
# ─────────────────────────────────────────

class Skill:
    """
    Define o contrato de uma skill.
    O que ela aceita, o que retorna, qual o risco.
    """
    def __init__(self, name: str, handler, risk: str = "LOW",
                 input_schema: dict = None, output_schema: dict = None):
        self.name          = name
        self.handler       = handler
        self.risk          = risk
        self.input_schema  = input_schema or {}
        self.output_schema = output_schema or {}

    def execute(self, context: dict) -> dict:
        """Executa a skill com o contexto fornecido"""
        return self.handler(context)

    def __repr__(self):
        return f"Skill({self.name}, risk={self.risk})"

# ─────────────────────────────────────────
# PACKAGE — representação em memória
# ─────────────────────────────────────────

class Package:
    """
    Pacote carregado em memória.
    Combina manifest + skills registradas.
    """

    def __init__(self, name: str, package_type: int,
                 version: str, author: str,
                 dependencies: list = None):
        self.name         = name
        self.package_type = package_type
        self.version      = version
        self.author       = author
        self.dependencies = dependencies or []
        self._skills      = {}

    def register_skill(self, skill: Skill):
        """Registra uma skill neste pacote"""
        self._skills[skill.name] = skill

    def get_skill(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    @property
    def skills(self) -> list:
        return list(self._skills.keys())

    def __repr__(self):
        return (
            f"Package({self.name}, "
            f"v{self.version}, "
            f"skills={self.skills})"
        )

# ─────────────────────────────────────────
# PACKAGE LOADER
# ─────────────────────────────────────────

class PackageLoader:
    """
    Carrega e valida pacotes .diovan.
    Resolve dependências antes de registrar no núcleo.
    """

    def __init__(self, nucleus):
        self.nucleus  = nucleus
        self._loaded  = {}

    def load_python_package(self, package: Package):
        """
        Carrega um pacote definido diretamente em Python.
        Usado enquanto o compilador .diovan não existe.
        Registra no núcleo automaticamente.
        """
        # Verifica dependências
        for dep in package.dependencies:
            if dep not in self.nucleus.get_loaded_packages():
                raise ImportError(
                    f"Dependência não encontrada: {dep} "
                    f"(requerida por {package.name})"
                )

        # Registra no núcleo
        self.nucleus.register_package(package.name, package)
        self._loaded[package.name] = package
        return package

    def load_diovan_file(self, path: Path) -> Package:
        """
        Carrega um arquivo .diovan binário.
        Valida assinatura e checksum antes de carregar.
        """
        with open(path, "rb") as f:
            data = f.read()

        # Valida assinatura
        if data[:4] != MAGIC_BYTES:
            raise ValueError(f"Assinatura inválida: {path}")

        # Extrai header
        package_type = struct.unpack("B", data[4:5])[0]
        version_byte = struct.unpack("B", data[5:6])[0]
        payload_size = struct.unpack(">I", data[10:14])[0]

        # Valida checksum
        payload_start = 18
        payload       = data[payload_start:payload_start + payload_size]
        checksum      = data[payload_start + payload_size:payload_start + payload_size + 4]
        expected      = hashlib.sha256(payload).digest()[:4]

        if checksum != expected:
            raise ValueError(f"Checksum inválido: {path} — pacote corrompido")

        # Parseia manifest
        separator      = b'\x00\xFF\x00\xFF'
        sep_idx        = payload.find(separator)
        manifest_bytes = payload[:sep_idx]
        manifest       = json.loads(manifest_bytes.decode("utf-8"))

        pkg = Package(
            name         = manifest["name"],
            package_type = package_type,
            version      = manifest["version"],
            author       = manifest["author"],
            dependencies = manifest.get("dependencies", []),
        )

        return self.load_python_package(pkg)

    def get_loaded(self) -> list:
        return list(self._loaded.keys())

    def is_loaded(self, name: str) -> bool:
        return name in self._loaded
