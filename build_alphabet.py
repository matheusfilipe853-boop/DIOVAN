"""
DIOVAN — Alphabet Builder v2
Extrai conceitos do conversations.json e gera language.diovan binário real.
Usa DiovanPackage para empacotar no formato oficial do protocolo.

Uso: python3 build_alphabet.py
"""

import json
import os
import re
import sys
from pathlib import Path
from collections import Counter
from dotenv import load_dotenv
import requests

# Importa o spec de pacotes
sys.path.insert(0, str(Path(__file__).parent))
from core.diovan_package_spec import DiovanPackage, PACKAGE_TYPES

load_dotenv()

# ─────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────

CONVERSATIONS_PATH = Path("./assets/conversations.json")
OUTPUT_PATH        = Path("./knowledge/language.diovan")
OLLAMA_URL         = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL       = os.getenv("DIOVAN_MODEL_ALPHABET", "diovan")

# ─────────────────────────────────────────
# EXTRATOR
# ─────────────────────────────────────────

def extract_user_text(conversations: list) -> list:
    texts = []
    for conv in conversations:
        mapping = conv.get("mapping", {})
        for node in mapping.values():
            msg = node.get("message")
            if not msg:
                continue
            if msg.get("author", {}).get("role") != "user":
                continue
            parts = msg.get("content", {}).get("parts", [])
            text  = " ".join([p for p in parts if isinstance(p, str)]).strip()
            if text and len(text) > 10:
                texts.append(text)
    return texts

def extract_key_phrases(texts: list) -> list:
    all_words = []
    for text in texts:
        words = re.findall(r'\b[a-záàãâéêíóôõúüçA-ZÁÀÃÂÉÊÍÓÔÕÚÜÇ]{3,}\b', text)
        all_words.extend([w.lower() for w in words])

    stopwords = {
        "que", "com", "para", "por", "uma", "como", "isso", "mais",
        "mas", "não", "sim", "ele", "ela", "nos", "ser", "ter",
        "seu", "sua", "dos", "das", "aos", "nas", "numa", "esse",
        "esta", "este", "essa", "aqui", "ali", "então", "também",
        "quando", "onde", "quem", "qual", "muito", "bem", "pode",
        "vai", "vou", "tem", "são", "está", "foi", "era", "você",
        "meu", "minha", "tenho", "fazer", "entre", "dia", "sem",
        "tempo", "cada", "todo", "toda", "isso", "aqui", "assim"
    }

    filtered = [w for w in all_words if w not in stopwords]
    counter  = Counter(filtered)
    return [word for word, _ in counter.most_common(80)]

# ─────────────────────────────────────────
# LLM — sem timeout, modelo diovan
# ─────────────────────────────────────────

def ask_ollama(prompt: str) -> str:
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_ctx"    : 8192,
                    "num_predict": 4096
                }
            },
            timeout=None  # sem timeout — aguarda o modelo terminar
        )
        return response.json().get("response", "").strip()
    except Exception as e:
        print(f"Erro Ollama: {e}")
        return ""

def group_concepts(words: list) -> list:
    words_str = ", ".join(words)

    prompt = f"""Você é o DIOVAN construindo seu alfabeto de conceitos primitivos em português brasileiro.

Analise estas palavras extraídas do histórico de conversas do criador Matheus:
{words_str}

Sua tarefa: agrupar em conceitos semânticos universais.

Regras obrigatórias:
- Gere entre 20 e 25 conceitos
- Nome do conceito em MAIÚSCULAS sem acentos (ex: AFIRMACAO, NAO_SABER)
- Cada conceito deve ter entre 3 e 8 palavras relacionadas
- Cubra todas as palavras fornecidas
- Conceitos devem ser primitivos e universais
- Retorne APENAS o array JSON abaixo, sem texto antes ou depois

Formato obrigatório:
[
  {{"conceito": "AFIRMACAO", "palavras": ["sim", "ok", "certo", "claro"]}},
  {{"conceito": "NEGACAO", "palavras": ["nao", "nunca", "jamais"]}}
]"""

    response = ask_ollama(prompt)

    # Extrai JSON da resposta
    try:
        match = re.search(r'\[.*?\]', response, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass

    try:
        clean = re.sub(r'```json|```', '', response).strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        print(f"Resposta parcial:\n{response[:400]}")
        return []

# ─────────────────────────────────────────
# INTEGRAÇÃO COM DiovanPackage
# ─────────────────────────────────────────

def build_language_package(concepts: list) -> DiovanPackage:
    """
    Cria um DiovanPackage do tipo LINGUAGEM (tipo 1)
    com os conceitos extraídos do conversations.json
    """
    pkg = DiovanPackage(
        name         = "language",
        author       = "Matheus F. Souza",
        package_type = 1  # LINGUAGEM — 4 bytes, 4 bilhões de endereços
    )

    # Reserva namespace para o pacote de linguagem
    pkg.manifest.reserve_namespace(prefix=1000, size=100_000)

    # Adiciona cada conceito como entrada
    for concept in concepts:
        nome    = concept.get("conceito", "DESCONHECIDO")
        palavras = concept.get("palavras", [])

        addr = pkg.add_entry(nome, {
            "palavras" : palavras,
            "idioma"   : "pt-BR",
            "versao"   : "1.0",
        })

        print(f"   {nome:20s} → endereço {addr:8d} | palavras: {', '.join(palavras[:3])}")

    return pkg

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def build():
    print("DIOVAN Alphabet Builder v2")
    print(f"Modelo: {OLLAMA_MODEL} | Timeout: indefinido")
    print("=" * 55)

    # 1. Carrega conversas
    print("\n1. Carregando conversations.json...")
    if not CONVERSATIONS_PATH.exists():
        print(f"Arquivo nao encontrado: {CONVERSATIONS_PATH}")
        sys.exit(1)

    with open(CONVERSATIONS_PATH, encoding="utf-8") as f:
        conversations = json.load(f)
    print(f"   {len(conversations)} conversas | modelo: {OLLAMA_MODEL}")

    # 2. Extrai texto
    print("\n2. Extraindo mensagens do usuario...")
    texts = extract_user_text(conversations)
    print(f"   {len(texts)} mensagens extraidas")

    # 3. Palavras-chave
    print("\n3. Identificando palavras-chave...")
    keywords = extract_key_phrases(texts)
    print(f"   {len(keywords)} palavras: {', '.join(keywords[:12])}")

    # 4. Agrupa conceitos
    print(f"\n4. Agrupando conceitos via {OLLAMA_MODEL}...")
    print("   Aguardando modelo (sem timeout)...")
    concepts = group_concepts(keywords)

    if not concepts:
        print("Modelo nao retornou conceitos validos")
        sys.exit(1)

    print(f"   {len(concepts)} conceitos identificados")

    # 5. Monta pacote DiovanPackage
    print("\n5. Montando language.diovan...")
    pkg = build_language_package(concepts)

    # 6. Salva
    print(f"\n6. Salvando pacote binario...")
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    pkg.save(OUTPUT_PATH)
    size = OUTPUT_PATH.stat().st_size
    print(f"   Salvo: {OUTPUT_PATH} ({size} bytes)")

    # 7. Valida
    print("\n7. Validando pacote...")
    from core.diovan_package_spec import DiovanPackage as DP
    pkg2 = DP.load(OUTPUT_PATH)
    print(f"   {pkg2}")
    print(f"   Checksum: OK")
    print(f"   Tipo: {PACKAGE_TYPES[1]['nome']}")
    print(f"   Entradas: {len(pkg2.lookup)}")

    # 8. Teste de busca
    print("\n8. Teste de busca:")
    for nome_busca in ["AFIRMACAO", "NEGACAO", "ACAO"]:
        addr, entry = pkg2.lookup.find_by_name(nome_busca)
        if addr is not None:
            palavras = entry["data"].get("palavras", [])[:3]
            print(f"   {nome_busca} → {addr} | {', '.join(palavras)}")

    print("\nlanguage.diovan gerado com sucesso!")
    print(f"Conceitos do vocabulario de Matheus F. Souza")
    print(f"Protocolo DIOVAN v1 | Tipo LINGUAGEM | {len(pkg2.lookup)} entradas")

if __name__ == "__main__":
    build()
