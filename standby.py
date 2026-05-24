"""
DIOVAN — Stand By Mode
Roda autonomamente, lê fontes de conhecimento,
gera pacotes de aprendizado sem interação humana.

Uso: python3 standby.py
Cron: 0 2 * * * cd ~/Documentos/diovan && source venv/bin/activate && python3 standby.py
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
import requests

load_dotenv()

# ─────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────

OLLAMA_URL   = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("DIOVAN_MODEL_NORMAL", "llama3.2")

KNOWLEDGE_DIR = Path("./knowledge")
STANDBY_LOG   = KNOWLEDGE_DIR / "standby_log.json"
RUST_DIR      = KNOWLEDGE_DIR / "rust-base"
RUST_PROFILE  = KNOWLEDGE_DIR / "rust_knowledge.md"

# ─────────────────────────────────────────
# LOGGER
# ─────────────────────────────────────────

def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = {"timestamp": timestamp, "level": level, "message": message}
    print(f"[{timestamp}] [{level}] {message}")

    logs = []
    if STANDBY_LOG.exists():
        with open(STANDBY_LOG) as f:
            logs = json.load(f)
    logs.append(entry)
    with open(STANDBY_LOG, "w") as f:
        json.dump(logs[-100:], f, indent=2, ensure_ascii=False)

# ─────────────────────────────────────────
# HASH DE ARQUIVO (detecta mudanças)
# ─────────────────────────────────────────

def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()

def load_processed_hashes() -> dict:
    hash_file = KNOWLEDGE_DIR / ".processed_hashes.json"
    if hash_file.exists():
        with open(hash_file) as f:
            return json.load(f)
    return {}

def save_processed_hashes(hashes: dict):
    hash_file = KNOWLEDGE_DIR / ".processed_hashes.json"
    with open(hash_file, "w") as f:
        json.dump(hashes, f, indent=2)

# ─────────────────────────────────────────
# OLLAMA
# ─────────────────────────────────────────

def ask_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.2, "num_ctx": 4096}
            },
            timeout=120
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        log(f"Erro Ollama: {e}", "ERROR")
        return ""

# ─────────────────────────────────────────
# PROCESSADOR DE CONHECIMENTO RUST
# ─────────────────────────────────────────

def process_rust_file(path: Path) -> str:
    content = path.read_text(encoding="utf-8")

    prompt = f"""Você é o DIOVAN processando conhecimento sobre Rust para sua base interna.

Leia o conteúdo abaixo e extraia:
1. Conceitos fundamentais presentes
2. Como cada conceito se relaciona com construção de sistemas de baixo nível
3. Como esse conhecimento pode ser usado para construir um parser binário
4. Pontos críticos para dominar Rust

Arquivo: {path.name}
Conteúdo:
{content[:3000]}

Responda em português de forma estruturada e técnica.
Foque no que é essencial para construir o protocolo DIOVAN em Rust."""

    return ask_ollama(prompt)

def synthesize_rust_knowledge(analyses: list) -> str:
    combined = "\n\n".join(analyses[:5])

    prompt = f"""Você é o DIOVAN sintetizando seu aprendizado sobre Rust.

Com base nas análises abaixo, gere um documento de conhecimento consolidado que responda:
1. O que você precisa saber de Rust para construir um parser binário de 8 bytes
2. Quais conceitos de Rust são mais críticos para o protocolo DIOVAN
3. Qual é o caminho de aprendizado recomendado
4. Quais são os primeiros exercícios práticos

Análises:
{combined}

Gere um documento estruturado em markdown que será sua base de conhecimento permanente sobre Rust."""

    return ask_ollama(prompt)

# ─────────────────────────────────────────
# STAND BY PRINCIPAL
# ─────────────────────────────────────────

def run_standby():
    log("DIOVAN stand by iniciado")

    processed = load_processed_hashes()
    new_analyses = []
    files_processed = 0

    # Processa arquivos Rust novos ou modificados
    if RUST_DIR.exists():
        rust_files = list(RUST_DIR.glob("*.md"))
        log(f"Encontrados {len(rust_files)} arquivos Rust para analisar")

        for rust_file in rust_files:
            current_hash = file_hash(rust_file)
            file_key = str(rust_file)

            if processed.get(file_key) == current_hash:
                log(f"Sem mudanças: {rust_file.name} — pulando")
                continue

            log(f"Processando: {rust_file.name}")
            analysis = process_rust_file(rust_file)

            if analysis:
                new_analyses.append(f"## {rust_file.name}\n\n{analysis}")
                processed[file_key] = current_hash
                files_processed += 1
                log(f"Concluído: {rust_file.name}")
            else:
                log(f"Falhou: {rust_file.name}", "WARN")

    if not new_analyses:
        log("Nenhum arquivo novo para processar. Stand by concluído.")
        return

    # Gera síntese consolidada
    log("Gerando síntese de conhecimento Rust...")
    synthesis = synthesize_rust_knowledge(new_analyses)

    # Salva ou atualiza o perfil de conhecimento Rust
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = f"""# DIOVAN — Base de Conhecimento: Rust
*Atualizado em: {timestamp}*
*Arquivos processados: {files_processed}*

---

## Síntese Consolidada

{synthesis}

---

## Análises Individuais

"""
    individual = "\n\n---\n\n".join(new_analyses)
    full_content = header + individual

    RUST_PROFILE.write_text(full_content, encoding="utf-8")
    save_processed_hashes(processed)

    log(f"Base de conhecimento Rust salva em: {RUST_PROFILE}")
    log(f"Stand by concluído. {files_processed} arquivo(s) processado(s).")

# ─────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────

if __name__ == "__main__":
    run_standby()
