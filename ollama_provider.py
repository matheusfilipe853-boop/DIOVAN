"""
DIOVAN — Provedor Ollama
Motor de linguagem substituível via .env ou parâmetro direto.
"""

import os
import requests
from dotenv import load_dotenv
from core.llm.providers.base_provider import BaseProvider

load_dotenv()

class OllamaProvider(BaseProvider):
    def __init__(self, model: str = None):
        self.model    = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.base_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

    def send(self, prompt: str, history: list = []) -> str:
        full_prompt = self._build_prompt(prompt, history)

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_ctx": 8192
                    }
                },
                timeout=120
            )
            return response.json().get("response", "").strip()

        except requests.exceptions.ConnectionError:
            return "❌ Ollama não está rodando. Execute 'ollama serve' primeiro."
        except requests.exceptions.Timeout:
            return "❌ Timeout. Tente uma pergunta mais curta."
        except Exception as e:
            return f"❌ Erro: {str(e)}"

    def _build_prompt(self, current_input: str, history: list) -> str:
        parts = []
        for msg in history[-10:]:
            role = "Usuário" if msg["role"] == "user" else "DIOVAN"
            parts.append(f"{role}: {msg['content']}")
        parts.append(f"Usuário: {current_input}")
        parts.append("DIOVAN:")
        return "\n".join(parts)
