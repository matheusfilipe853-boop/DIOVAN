#!/bin/bash

# ===========================================
# Setup do Projeto: Assistente de IA Local
# ===========================================

PROJECT_NAME="diovan"  # Troque o nome se quiser

echo "🚀 Criando estrutura do projeto: $PROJECT_NAME"

mkdir -p $PROJECT_NAME

cd $PROJECT_NAME

# ===========================================
# CAMADA 1: INTERFACE (Frontend / GUI)
# ===========================================
mkdir -p interface/desktop
mkdir -p interface/assets

cat > interface/desktop/app.py << 'EOF'
"""
Interface gráfica principal do assistente.
Responsável APENAS por capturar entrada (voz/texto) e exibir saída.
Não executa lógica de IA ou comandos do sistema aqui.
"""

# TODO: Implementar com PyQt5 ou Tkinter
# from core.orchestrator import Orchestrator

class App:
    def __init__(self):
        pass

    def run(self):
        pass
EOF

# ===========================================
# CAMADA 2: CORE (Orquestrador central)
# ===========================================
mkdir -p core

cat > core/__init__.py << 'EOF'
# Módulo central do assistente
EOF

cat > core/orchestrator.py << 'EOF'
"""
Orquestrador principal.
Recebe intenção da LLM e decide qual executor chamar.
É o cérebro de ligação entre LLM e executores.
"""

from core.llm.llm_interface import LLMInterface
from core.speech.stt import SpeechToText
from core.speech.tts import TextToSpeech

class Orchestrator:
    def __init__(self):
        self.llm = LLMInterface()
        self.stt = SpeechToText()
        self.tts = TextToSpeech()

    def listen_and_respond(self):
        """Fluxo principal: voz → texto → LLM → executor → resposta"""
        # 1. Captura voz e converte em texto
        text = self.stt.transcribe()

        # 2. Envia para LLM e recebe intenção estruturada
        response = self.llm.process(text)

        # 3. Executa ação baseada na intenção
        # TODO: roteamento para executores

        # 4. Responde por voz
        self.tts.speak(response)
EOF

# ===========================================
# CAMADA 3: LLM (Interface com modelos de IA)
# ===========================================
mkdir -p core/llm

cat > core/llm/__init__.py << 'EOF'
EOF

cat > core/llm/llm_interface.py << 'EOF'
"""
Interface abstrata para modelos de linguagem.
Troca entre Ollama local e APIs externas (Claude, GPT)
sem precisar refatorar o resto do projeto.
"""

from core.llm.providers.ollama_provider import OllamaProvider
# from core.llm.providers.claude_provider import ClaudeProvider  # Futuro

class LLMInterface:
    def __init__(self, provider="ollama"):
        if provider == "ollama":
            self.provider = OllamaProvider()
        # elif provider == "claude":
        #     self.provider = ClaudeProvider()

    def process(self, text: str) -> str:
        return self.provider.send(text)
EOF

mkdir -p core/llm/providers

cat > core/llm/providers/__init__.py << 'EOF'
EOF

cat > core/llm/providers/base_provider.py << 'EOF'
"""
Classe base para todos os provedores de LLM.
Qualquer novo provedor (Ollama, Claude, GPT) herda daqui.
Garante que a interface seja sempre a mesma.
"""

from abc import ABC, abstractmethod

class BaseProvider(ABC):
    @abstractmethod
    def send(self, prompt: str) -> str:
        """Envia prompt e retorna resposta como string"""
        pass
EOF

cat > core/llm/providers/ollama_provider.py << 'EOF'
"""
Provedor Ollama - roda localmente, sem internet.
Conecta via API REST local na porta 11434.
"""

import requests
from core.llm.providers.base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    def __init__(self, model="llama3", base_url="http://localhost:11434"):
        self.model = model
        self.base_url = base_url

    def send(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model, "prompt": prompt, "stream": False}
        )
        return response.json().get("response", "")
EOF

# ===========================================
# CAMADA 4: SPEECH (Voz: entrada e saída)
# ===========================================
mkdir -p core/speech

cat > core/speech/__init__.py << 'EOF'
EOF

cat > core/speech/stt.py << 'EOF'
"""
Speech-to-Text: converte voz em texto usando Whisper.
Roda 100% local, sem internet.
"""

import whisper

class SpeechToText:
    def __init__(self, model_size="base"):
        # Modelos disponíveis: tiny, base, small, medium, large
        # tiny/base = mais leve, small/medium = mais preciso
        self.model = whisper.load_model(model_size)

    def transcribe(self, audio_path: str = None) -> str:
        """
        Se audio_path for None, grava do microfone.
        Se for um arquivo, transcreve o arquivo.
        """
        # TODO: implementar gravação do microfone
        if audio_path:
            result = self.model.transcribe(audio_path)
            return result["text"]
        return ""
EOF

cat > core/speech/tts.py << 'EOF'
"""
Text-to-Speech: converte texto em voz.
Troca fácil entre Piper (local) e outras engines.
"""

class TextToSpeech:
    def __init__(self, engine="piper"):
        self.engine = engine

    def speak(self, text: str):
        """Reproduz o texto como áudio"""
        # TODO: implementar com Piper ou similar
        print(f"[TTS] {text}")  # Placeholder por enquanto
EOF

# ===========================================
# CAMADA 5: EXECUTORES (Ações no sistema)
# ===========================================
mkdir -p executors/system
mkdir -p executors/git
mkdir -p executors/files

cat > executors/__init__.py << 'EOF'
EOF

cat > executors/base_executor.py << 'EOF'
"""
Classe base para todos os executores.
Garante interface padronizada independente do que o executor faz.
"""

from abc import ABC, abstractmethod

class BaseExecutor(ABC):
    @abstractmethod
    def execute(self, command: dict) -> dict:
        """
        Recebe um comando estruturado e retorna resultado.
        command: { "action": "...", "params": {...} }
        result:  { "success": bool, "output": "..." }
        """
        pass
EOF

cat > executors/system/system_executor.py << 'EOF'
"""
Executor de comandos do sistema operacional.
Usa adaptadores para funcionar em Linux, Windows, Mac.
"""

from executors.base_executor import BaseExecutor
from adapters.adapter_factory import AdapterFactory

class SystemExecutor(BaseExecutor):
    def __init__(self):
        self.adapter = AdapterFactory.get_adapter()

    def execute(self, command: dict) -> dict:
        action = command.get("action")
        params = command.get("params", {})

        return self.adapter.run(action, params)
EOF

cat > executors/git/git_executor.py << 'EOF'
"""
Executor de operações Git/GitHub.
Ex: clonar repositório, criar branch, fazer commit, etc.
"""

import subprocess
from executors.base_executor import BaseExecutor

class GitExecutor(BaseExecutor):
    def execute(self, command: dict) -> dict:
        action = command.get("action")
        params = command.get("params", {})

        if action == "clone":
            return self._clone(params.get("url"), params.get("path", "."))
        elif action == "status":
            return self._status(params.get("path", "."))

        return {"success": False, "output": f"Ação desconhecida: {action}"}

    def _clone(self, url: str, path: str) -> dict:
        result = subprocess.run(["git", "clone", url, path], capture_output=True, text=True)
        return {"success": result.returncode == 0, "output": result.stdout or result.stderr}

    def _status(self, path: str) -> dict:
        result = subprocess.run(["git", "-C", path, "status"], capture_output=True, text=True)
        return {"success": result.returncode == 0, "output": result.stdout}
EOF

# ===========================================
# CAMADA 6: ADAPTADORES (Abstração de SO)
# ===========================================
mkdir -p adapters/linux
mkdir -p adapters/windows
mkdir -p adapters/mac

cat > adapters/__init__.py << 'EOF'
EOF

cat > adapters/base_adapter.py << 'EOF'
"""
Adaptador base abstrato.
Define contrato que todo SO precisa implementar.
Permite trocar Linux por Windows sem refatorar o resto.
"""

from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    def run(self, action: str, params: dict) -> dict:
        pass

    @abstractmethod
    def get_system_info(self) -> dict:
        pass
EOF

cat > adapters/adapter_factory.py << 'EOF'
"""
Factory que detecta o SO e retorna o adaptador correto.
O resto do código nunca precisa saber qual SO está rodando.
"""

import platform
from adapters.base_adapter import BaseAdapter

class AdapterFactory:
    @staticmethod
    def get_adapter() -> BaseAdapter:
        system = platform.system()

        if system == "Linux":
            from adapters.linux.linux_adapter import LinuxAdapter
            return LinuxAdapter()
        elif system == "Windows":
            from adapters.windows.windows_adapter import WindowsAdapter
            return WindowsAdapter()
        elif system == "Darwin":
            from adapters.mac.mac_adapter import MacAdapter
            return MacAdapter()
        else:
            raise Exception(f"Sistema operacional não suportado: {system}")
EOF

cat > adapters/linux/linux_adapter.py << 'EOF'
"""
Adaptador Linux.
Implementa ações específicas do Linux/Ubuntu.
"""

import subprocess
from adapters.base_adapter import BaseAdapter

class LinuxAdapter(BaseAdapter):
    def run(self, action: str, params: dict) -> dict:
        if action == "shell":
            cmd = params.get("command", "")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            return {"success": result.returncode == 0, "output": result.stdout or result.stderr}

        return {"success": False, "output": f"Ação não implementada: {action}"}

    def get_system_info(self) -> dict:
        result = subprocess.run("uname -a", shell=True, capture_output=True, text=True)
        return {"os": "Linux", "info": result.stdout.strip()}
EOF

cat > adapters/windows/windows_adapter.py << 'EOF'
"""
Adaptador Windows.
TODO: implementar quando necessário.
"""

from adapters.base_adapter import BaseAdapter

class WindowsAdapter(BaseAdapter):
    def run(self, action: str, params: dict) -> dict:
        # TODO: implementar com subprocess e powershell
        return {"success": False, "output": "Windows adapter não implementado ainda"}

    def get_system_info(self) -> dict:
        return {"os": "Windows"}
EOF

cat > adapters/mac/mac_adapter.py << 'EOF'
"""
Adaptador macOS.
TODO: implementar quando necessário.
"""

from adapters.base_adapter import BaseAdapter

class MacAdapter(BaseAdapter):
    def run(self, action: str, params: dict) -> dict:
        # TODO: implementar
        return {"success": False, "output": "Mac adapter não implementado ainda"}

    def get_system_info(self) -> dict:
        return {"os": "macOS"}
EOF

# ===========================================
# CAMADA 7: MEMÓRIA (Base de conhecimento)
# ===========================================
mkdir -p memory/local
mkdir -p memory/cloud

cat > memory/__init__.py << 'EOF'
EOF

cat > memory/memory_manager.py << 'EOF'
"""
Gerenciador de memória e contexto.
Decide se usa base local (offline) ou nuvem (online).
"""

class MemoryManager:
    def __init__(self, mode="local"):
        self.mode = mode  # "local" ou "cloud"

    def store(self, key: str, value: str):
        """Armazena informação na base de conhecimento"""
        # TODO: implementar com SQLite (local) ou API (cloud)
        pass

    def retrieve(self, query: str) -> str:
        """Busca informação relevante para o contexto"""
        # TODO: implementar busca semântica
        pass
EOF

# ===========================================
# CONFIGURAÇÕES
# ===========================================
mkdir -p config

cat > config/settings.py << 'EOF'
"""
Configurações centrais do projeto.
Altere aqui sem precisar mexer no código.
"""

# Modelo LLM
LLM_PROVIDER = "ollama"       # "ollama" | "claude" | "openai"
LLM_MODEL = "llama3"          # modelo local do Ollama

# Speech
STT_MODEL = "base"            # "tiny" | "base" | "small" | "medium" | "large"
TTS_ENGINE = "piper"          # engine de síntese de voz

# Memória
MEMORY_MODE = "local"         # "local" | "cloud" | "hybrid"

# Servidor (para uso remoto via celular)
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000
EOF

# ===========================================
# PONTO DE ENTRADA
# ===========================================
cat > main.py << 'EOF'
"""
Ponto de entrada do assistente.
Inicia o orquestrador e a interface.
"""

from core.orchestrator import Orchestrator

if __name__ == "__main__":
    print("🤖 Iniciando assistente...")
    orchestrator = Orchestrator()
    orchestrator.listen_and_respond()
EOF

# ===========================================
# DEPENDÊNCIAS
# ===========================================
cat > requirements.txt << 'EOF'
# LLM
requests>=2.31.0

# Speech-to-Text
openai-whisper>=20231117

# Text-to-Speech
# piper-tts  # instalar separado se necessário

# Interface
# PyQt5>=5.15.0  # descomentar quando for criar a GUI

# Utilitários
python-dotenv>=1.0.0
EOF

cat > .env.example << 'EOF'
# Copie este arquivo para .env e preencha
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama3
MEMORY_MODE=local

# Para modo cloud (opcional)
# ANTHROPIC_API_KEY=
# OPENAI_API_KEY=
EOF

cat > .gitignore << 'EOF'
.env
__pycache__/
*.pyc
*.pyo
.venv/
venv/
*.egg-info/
.DS_Store
EOF

# README
cat > README.md << 'EOF'
# Assistente de IA Local

Assistente pessoal com voz, rodando localmente com Ollama + Whisper.

## Estrutura

```
diovan/
├── interface/      # GUI desktop
├── core/
│   ├── llm/        # Interface com modelos de linguagem (Ollama, Claude, etc)
│   ├── speech/     # Voz: STT (Whisper) e TTS
│   └── orchestrator.py  # Orquestrador central
├── executors/      # Executores de ações (sistema, git, arquivos)
├── adapters/       # Abstração de sistemas operacionais
├── memory/         # Base de conhecimento local e cloud
└── config/         # Configurações
```

## Como rodar

```bash
python main.py
```
EOF

echo ""
echo "✅ Estrutura criada com sucesso!"
echo ""
echo "📁 Abra a pasta '$PROJECT_NAME' no VS Code:"
echo "   code $PROJECT_NAME"
echo ""
