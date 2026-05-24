"""
DIOVAN — Runtime configuration
All timeouts and model settings in one place.
Change here, affects everywhere.
"""

import os
from dotenv import load_dotenv
load_dotenv()

# Ollama timeouts
OLLAMA_CONNECT_TIMEOUT = int(os.getenv("OLLAMA_CONNECT_TIMEOUT", "5"))
OLLAMA_READ_TIMEOUT    = int(os.getenv("OLLAMA_READ_TIMEOUT", "666"))

# Context size per model level
OLLAMA_CTX_FAST    = int(os.getenv("OLLAMA_CTX_FAST",    "2048"))
OLLAMA_CTX_NORMAL  = int(os.getenv("OLLAMA_CTX_NORMAL",  "4096"))
OLLAMA_CTX_COMPLEX = int(os.getenv("OLLAMA_CTX_COMPLEX", "8192"))

# GitHub
GITHUB_TIMEOUT = int(os.getenv("GITHUB_TIMEOUT", "10"))

# TTS
TTS_PLAYBACK_TIMEOUT = int(os.getenv("TTS_PLAYBACK_TIMEOUT", "120"))
