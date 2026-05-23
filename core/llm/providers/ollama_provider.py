"""
DIOVAN — Provedor Ollama
Motor de linguagem substituível via .env ou parâmetro direto.
"""

import os
import requests
from dotenv import load_dotenv
from core.llm.providers.base_provider import BaseProvider
from config.runtime import (
    OLLAMA_CONNECT_TIMEOUT,
    OLLAMA_READ_TIMEOUT,
    OLLAMA_CTX_NORMAL
)

load_dotenv()

class OllamaProvider(BaseProvider):
    def __init__(self, model: str = None):
        self.model    = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.num_ctx  = OLLAMA_CTX_NORMAL

    def send(self, prompt: str, history: list = [], on_token=None) -> str:
        full_prompt = self._build_prompt(prompt, history)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": True,
                    "options": {
                        "temperature": 0.3,
                        "num_ctx": self.num_ctx
                    }
                },
                stream=True,
                timeout=(OLLAMA_CONNECT_TIMEOUT, OLLAMA_READ_TIMEOUT)
            )

            full_response = ""
            for line in response.iter_lines():
                if not line:
                    continue
                import json
                chunk = json.loads(line)
                token = chunk.get("response", "")
                full_response += token
                if on_token:
                    on_token(token)
                if chunk.get("done"):
                    break

            return full_response.strip()

        except requests.exceptions.ConnectionError:
            return "❌ Ollama não está rodando."
        except requests.exceptions.Timeout:
            return "❌ Timeout. Tente uma pergunta mais curta."
        except Exception as e:
            return f"❌ Erro: {str(e)}"

    def _build_prompt(self, current_input: str, history: list) -> str:
        identity = (
            "Você é DIOVAN — Domine Intelligent Omni Vitae Agent Neural.\n"
            "O senhor da inteligência neural onipresente viva.\n"
            "Responda sempre em português. Nunca invente informações. "
            "Se não souber, diga claramente.\n\n"
        )
        parts = [identity]
        for msg in history[-10:]:
            role = "Usuário" if msg["role"] == "user" else "DIOVAN"
            parts.append(f"{role}: {msg['content']}")
        parts.append(f"Usuário: {current_input}")
        parts.append("DIOVAN:")
        return "\n".join(parts)
