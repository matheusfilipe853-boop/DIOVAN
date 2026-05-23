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
