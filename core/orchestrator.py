"""
DIOVAN — Orquestrador com roteamento inteligente de modelos.
Três níveis de processamento baseados na complexidade da pergunta.

Nível 1 — gemma2:2b    → respostas simples, saudações, confirmações
Nível 2 — llama3.2     → dia a dia, código, consultas GitHub
Nível 3 — diovan       → arquitetura, análises complexas, decisões críticas
"""

import os
from core.llm.llm_interface import LLMInterface
from executors.github.github_executor import GitHubExecutor
from executors.files.file_executor import FileExecutor

# Triggers para busca no GitHub
GITHUB_TRIGGERS = [
    "commit", "commits", "repositório", "repo", "issue", "issues",
    "pull request", "pr", "deploy", "deployment", "branch",
    "semana", "mudou", "alterou", "atualiz", "atividade",
    "implementado", "implementação", "como está", "como funciona",
    "onde está", "me mostra", "oauth", "auth", "stripe", "nextauth"
]

# Triggers para leitura de arquivos locais
FILE_TRIGGERS = [
    "leia o arquivo", "ler o arquivo", "leia o roadmap", "ler o roadmap",
    "knowledge", "base de conhecimento", "arquivo local", "leia o vision",
    "ler o vision", "diovan_roadmap", "diovan_vision", "onde se encontra",
    "qual fase", "em que fase", "sua fase", "seu roadmap", "seu status",
    "o que você é", "quem é você", "seu manifesto", "sua visão",
    "avalia", "avalie", "próprio roadmap", "seu próprio",
    "como você avalia", "autoavalia",
    "quem sou", "além de desenvolvedor", "meu perfil", "sobre mim",
    "souzabank", "imperinvest", "m.f souza", "minha identidade",
    "meus projetos", "minha visão", "minha estratégia", "profile"
]

# Arquivos de conhecimento do DIOVAN
KNOWLEDGE_FILES = {
    "roadmap"  : "knowledge/DIOVAN_ROADMAP.md",
    "vision"   : "knowledge/DIOVAN_VISION.md",
    "manifesto": "knowledge/DIOVAN_VISION.md",
    "status"   : "knowledge/DIOVAN_ROADMAP.md",
    "fase"     : "knowledge/DIOVAN_ROADMAP.md",
    "profile"  : "knowledge/profile.md",
    "souzabank": "knowledge/profile.md",
    "identidade": "knowledge/profile.md",
    "além"     : "knowledge/profile.md",
    "quem sou" : "knowledge/profile.md",
    "sobre mim": "knowledge/profile.md",
}

# Palavras que indicam complexidade alta → Nível 3
COMPLEX_TRIGGERS = [
    "arquitete", "arquitetura", "analise", "análise", "compare",
    "explique em detalhes", "como funciona", "por que", "diferença entre",
    "melhor forma", "estratégia", "estrutura", "decisão", "trade-off",
    "implemente", "refatore", "otimize", "debug", "erro complexo",
    "visão", "manifesto", "roadmap", "futuro do projeto"
]

# Palavras que indicam simplicidade → Nível 1
SIMPLE_TRIGGERS = [
    "oi", "olá", "tudo bem", "ok", "sim", "não", "obrigado",
    "valeu", "certo", "entendi", "pode", "claro", "legal",
    "status", "hora", "data", "ping", "teste"
]


class Orchestrator:
    def __init__(self):
        self.github  = GitHubExecutor()
        self.files   = FileExecutor()
        self.history = []
        self._models = {}  # cache lazy

    def _get_model(self, model_name: str) -> LLMInterface:
        if model_name not in self._models:
            self._models[model_name] = LLMInterface(model=model_name)
        return self._models[model_name]

    def _select_model(self, text: str) -> tuple:
        text_lower = text.lower().strip()
        word_count = len(text_lower.split())

        if word_count <= 3 or any(t in text_lower for t in SIMPLE_TRIGGERS):
            model = os.getenv("DIOVAN_MODEL_FAST", "gemma2:2b")
            return self._get_model(model), "⚡ Nível 1"

        if word_count > 20 or any(t in text_lower for t in COMPLEX_TRIGGERS):
            model = os.getenv("DIOVAN_MODEL_COMPLEX", "diovan")
            return self._get_model(model), "🧠 Nível 3"

        model = os.getenv("DIOVAN_MODEL_NORMAL", "llama3.2")
        return self._get_model(model), "💡 Nível 2"

    def chat(self, user_input: str, on_token=None) -> str:
        context = self._fetch_context(user_input)
        llm, level = self._select_model(user_input)

        print(f" {level}", end="", flush=True)

        enriched_input = user_input
        if context:
            enriched_input = f"O usuário perguntou: {user_input}\n\nContexto:\n{context}\n\nResponda em português."

        self.history.append({"role": "user", "content": user_input})
        response = llm.process(enriched_input, self.history, on_token=on_token)
        self.history.append({"role": "assistant", "content": response})

        return response

    def _fetch_context(self, text: str) -> str:
        text_lower = text.lower()

        if any(trigger in text_lower for trigger in FILE_TRIGGERS):
            return self._fetch_file_context(text_lower)

        if any(trigger in text_lower for trigger in GITHUB_TRIGGERS):
            return self._fetch_github_context(text, text_lower)

        return None

    def _fetch_file_context(self, text_lower: str) -> str:
        target_file = None
        for keyword, filepath in KNOWLEDGE_FILES.items():
            if keyword in text_lower:
                target_file = filepath
                break

        if not target_file:
            target_file = "knowledge/DIOVAN_ROADMAP.md"

        if not os.path.exists(target_file):
            return f"Arquivo {target_file} não encontrado."

        print(f"\n📂 Lendo: {target_file}", end="", flush=True)
        max_chars = 3000 if "profile" in target_file else 1000

        result = self.files.execute({
            "params": {
                "path": target_file,
                "max_chars": max_chars
            }
        })

        if result.get("success"):
            identity_anchor = (
                "O usuário está perguntando sobre SI MESMO, não sobre o DIOVAN.\n"
                "Use o perfil abaixo para responder sobre quem é o Matheus, "
                "seus projetos, sua visão e sua identidade.\n\n"
            )
            return identity_anchor + result.get("output", "")

        return None

    def _fetch_github_context(self, text: str, text_lower: str) -> str:
        print("\n🔍 GitHub...", end="", flush=True)

        keywords = self._extract_search_term(text)
        if keywords and len(keywords) > 3:
            result = self.github.execute({
                "action": "search_file",
                "params": {"query": keywords}
            })
            if result.get("success"):
                return result.get("output", "")

        if any(w in text_lower for w in ["semana", "atividade", "resumo"]):
            result = self.github.execute({"action": "weekly_activity"})
        elif any(w in text_lower for w in ["commit", "commits", "mudou"]):
            result = self.github.execute({"action": "recent_commits", "params": {"days": 7}})
        elif any(w in text_lower for w in ["issue", "issues", "bug"]):
            result = self.github.execute({"action": "open_issues"})
        elif any(w in text_lower for w in ["pull request", "pr", "merge"]):
            result = self.github.execute({"action": "pull_requests"})
        elif any(w in text_lower for w in ["deploy", "deployment"]):
            result = self.github.execute({"action": "deployments"})
        elif any(w in text_lower for w in ["estrutura", "pasta"]):
            result = self.github.execute({"action": "file_structure"})
        else:
            result = self.github.execute({"action": "repo_summary"})

        if result.get("success"):
            return result.get("output", "")

        return None

    def _extract_search_term(self, text: str) -> str:
        stop_words = [
            "como", "está", "implementado", "implementação", "o", "a", "de",
            "no", "na", "do", "da", "me", "mostra", "código", "arquivo",
            "projeto", "funciona", "onde", "que", "foi", "qual", "quais",
            "leia", "ler", "diga", "conta", "explica", "sobre"
        ]
        words = text.lower().split()
        keywords = [w for w in words if w not in stop_words and len(w) > 3]
        return " ".join(keywords[:3])

    def run_text_mode(self):
        print("🤖 DIOVAN iniciado. Digite 'sair' para encerrar.\n")

        while True:
            try:
                user_input = input("Você: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ["sair", "exit", "quit"]:
                    print("👋 Encerrando DIOVAN...")
                    break

                print("⏳ Processando...", end="", flush=True)
                response = self.chat(user_input)
                print(f"\n\n🤖 DIOVAN: {response}\n")

            except KeyboardInterrupt:
                print("\n👋 Encerrando DIOVAN...")
                break
