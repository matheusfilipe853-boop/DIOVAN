"""
DIOVAN — Knowledge Builder
Processa conversations.json do ChatGPT e conduz entrevista de calibração.
Salva base de conhecimento curada em knowledge/profile.md

Uso: python3 build_knowledge.py --source ~/Downloads/conversations.json
"""

import json
import os
import re
import argparse
from datetime import datetime

# ─────────────────────────────────────────
# PARSER DE CONVERSAS
# ─────────────────────────────────────────

def load_conversations(path: str) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def extract_messages(conv: dict) -> list:
    mapping = conv.get("mapping", {})
    messages = []
    for node in mapping.values():
        msg = node.get("message")
        if not msg:
            continue
        role = msg.get("author", {}).get("role", "")
        if role not in ["user", "assistant"]:
            continue
        parts = msg.get("content", {}).get("parts", [])
        text = " ".join([p for p in parts if isinstance(p, str)]).strip()
        if text and len(text) > 50:
            messages.append({"role": role, "text": text})
    return messages

def extract_topics(conversations: list) -> list:
    """Extrai tópicos principais de cada conversa"""
    topics = []
    for conv in conversations:
        title    = conv.get("title", "Sem título")
        messages = extract_messages(conv)
        if not messages:
            continue

        # Pega as primeiras mensagens do usuário como contexto
        user_msgs = [m["text"] for m in messages if m["role"] == "user"][:3]
        context   = " | ".join(user_msgs)[:500] if user_msgs else ""

        # Resumo das mensagens do assistant (insights)
        asst_msgs = [m["text"] for m in messages if m["role"] == "assistant"][:2]
        insights  = asst_msgs[0][:300] if asst_msgs else ""

        topics.append({
            "title"   : title,
            "context" : context,
            "insights": insights,
            "total"   : len(messages),
        })

    return topics


# ─────────────────────────────────────────
# INTERFACE DE CALIBRAÇÃO
# ─────────────────────────────────────────

class Colors:
    RESET  = "\033[0m"
    CYAN   = "\033[96m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    WHITE  = "\033[97m"

SEP = f"{Colors.DIM}{'─' * 60}{Colors.RESET}"

def print_banner():
    os.system("clear")
    print(f"""
{Colors.CYAN}{Colors.BOLD}
  DIOVAN — Modo Calibração
  Construindo sua base de conhecimento pessoal
{Colors.RESET}
{SEP}
{Colors.DIM}  Este processo vai te apresentar os temas identificados
  nas suas conversas com o ChatGPT, um por um.
  Você valida, corrige ou descarta cada um.
  O resultado é salvo em knowledge/profile.md{Colors.RESET}
{SEP}
""")

def ask(prompt: str, options: list = None) -> str:
    if options:
        opts = " / ".join([f"{Colors.CYAN}{o}{Colors.RESET}" for o in options])
        print(f"\n{Colors.YELLOW}> {prompt}{Colors.RESET} [{opts}] ", end="")
    else:
        print(f"\n{Colors.YELLOW}> {prompt}{Colors.RESET}\n  ", end="")
    return input().strip().lower()


# ─────────────────────────────────────────
# CATEGORIAS DE CONHECIMENTO
# ─────────────────────────────────────────

CATEGORIES = [
    "identidade_pessoal",
    "estrategia_negocios",
    "desenvolvimento_tecnico",
    "financas_investimentos",
    "visao_geopolitica",
    "projetos_ativos",
    "habilidades",
    "outros",
]

knowledge_base = {cat: [] for cat in CATEGORIES}
knowledge_base["meta"] = {
    "gerado_em"    : datetime.now().isoformat(),
    "total_temas"  : 0,
    "total_aceitos": 0,
}


# ─────────────────────────────────────────
# LOOP DE CALIBRAÇÃO
# ─────────────────────────────────────────

def calibrate(topics: list, output_path: str):
    print_banner()
    print(f"{Colors.WHITE}  Encontrei {len(topics)} conversas para analisar.{Colors.RESET}")
    print(f"{Colors.WHITE}  Vamos começar. Digite Ctrl+C a qualquer momento para salvar e sair.{Colors.RESET}\n")

    input(f"  {Colors.DIM}Pressione Enter para começar...{Colors.RESET}")

    accepted = []
    skipped  = 0

    for i, topic in enumerate(topics):
        os.system("clear")
        print(f"\n{Colors.CYAN}{Colors.BOLD}  Tema {i+1} de {len(topics)}{Colors.RESET}")
        print(SEP)
        print(f"\n{Colors.BOLD}  Título:{Colors.RESET} {topic['title']}")

        if topic["context"]:
            print(f"\n{Colors.DIM}  Contexto:{Colors.RESET}")
            print(f"  {topic['context'][:300]}")

        if topic["insights"]:
            print(f"\n{Colors.DIM}  Insight principal:{Colors.RESET}")
            print(f"  {topic['insights'][:300]}")

        print(f"\n{Colors.DIM}  {topic['total']} mensagens nesta conversa{Colors.RESET}")
        print(f"\n{SEP}")

        action = ask(
            "O que fazer com este tema?",
            ["aceitar", "editar", "descartar", "pular"]
        )

        if action in ["a", "aceitar"]:
            # Escolhe categoria
            print(f"\n{Colors.WHITE}  Categorias disponíveis:{Colors.RESET}")
            for j, cat in enumerate(CATEGORIES):
                print(f"  {j+1}. {cat}")

            cat_input = ask("Número da categoria")
            try:
                cat_idx = int(cat_input) - 1
                category = CATEGORIES[cat_idx] if 0 <= cat_idx < len(CATEGORIES) else "outros"
            except ValueError:
                category = "outros"

            note = ask("Adicione uma nota pessoal sobre este tema (ou Enter para pular)")

            entry = {
                "titulo"   : topic["title"],
                "contexto" : topic["context"][:500],
                "insight"  : topic["insights"][:500],
                "nota"     : note if note else None,
            }
            knowledge_base[category].append(entry)
            accepted.append(entry)
            print(f"\n  {Colors.GREEN}✓ Salvo em '{category}'{Colors.RESET}")

        elif action in ["e", "editar"]:
            titulo = ask(f"Novo título (atual: {topic['title']})")
            if not titulo:
                titulo = topic["title"]

            resumo = ask("Descreva este conhecimento com suas palavras")
            note   = ask("Categoria (ou Enter para 'outros')")
            category = note if note in CATEGORIES else "outros"

            entry = {
                "titulo"   : titulo,
                "contexto" : resumo,
                "insight"  : "",
                "nota"     : "Editado manualmente",
            }
            knowledge_base[category].append(entry)
            accepted.append(entry)
            print(f"\n  {Colors.GREEN}✓ Salvo com edição em '{category}'{Colors.RESET}")

        elif action in ["d", "descartar"]:
            print(f"\n  {Colors.DIM}Descartado.{Colors.RESET}")
            skipped += 1

        else:
            print(f"\n  {Colors.DIM}Pulado.{Colors.RESET}")
            skipped += 1

        import time
        time.sleep(0.5)

    # Atualiza meta
    knowledge_base["meta"]["total_temas"]   = len(topics)
    knowledge_base["meta"]["total_aceitos"] = len(accepted)

    # Salva
    save_knowledge(output_path)

    print(f"\n{SEP}")
    print(f"\n{Colors.GREEN}{Colors.BOLD}  Calibração concluída!{Colors.RESET}")
    print(f"  {len(accepted)} temas aceitos | {skipped} descartados/pulados")
    print(f"  Base salva em: {output_path}\n")


# ─────────────────────────────────────────
# SALVAR BASE DE CONHECIMENTO
# ─────────────────────────────────────────

def save_knowledge(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    lines = [
        "# DIOVAN — Base de Conhecimento Pessoal",
        f"*Gerado em: {knowledge_base['meta']['gerado_em']}*",
        f"*Total de temas: {knowledge_base['meta']['total_aceitos']}*",
        "",
        "---",
        "",
    ]

    category_labels = {
        "identidade_pessoal"    : "## Identidade Pessoal",
        "estrategia_negocios"   : "## Estratégia e Negócios",
        "desenvolvimento_tecnico": "## Desenvolvimento Técnico",
        "financas_investimentos" : "## Finanças e Investimentos",
        "visao_geopolitica"     : "## Visão Geopolítica",
        "projetos_ativos"       : "## Projetos Ativos",
        "habilidades"           : "## Habilidades",
        "outros"                : "## Outros",
    }

    for cat, label in category_labels.items():
        entries = knowledge_base.get(cat, [])
        if not entries:
            continue

        lines.append(label)
        lines.append("")

        for entry in entries:
            lines.append(f"### {entry['titulo']}")
            if entry.get("contexto"):
                lines.append(f"{entry['contexto']}")
            if entry.get("insight"):
                lines.append(f"\n**Insight:** {entry['insight']}")
            if entry.get("nota"):
                lines.append(f"\n**Nota pessoal:** {entry['nota']}")
            lines.append("")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DIOVAN Knowledge Builder")
    parser.add_argument("--source",  default="~/Downloads/conversations.json")
    parser.add_argument("--output",  default="./knowledge/profile.md")
    args = parser.parse_args()

    source = os.path.expanduser(args.source)

    print(f"\nCarregando {source}...")
    conversations = load_conversations(source)
    topics        = extract_topics(conversations)

    print(f"{len(topics)} conversas encontradas.")

    try:
        calibrate(topics, args.output)
    except KeyboardInterrupt:
        print(f"\n\nSalvando progresso...")
        save_knowledge(args.output)
        print(f"Salvo em {args.output}")
