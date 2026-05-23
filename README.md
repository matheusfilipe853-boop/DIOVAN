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
