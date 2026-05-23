#!/bin/bash
set -e

echo "🔀 Instalando roteador de modelos DIOVAN..."

cp orchestrator.py ./core/orchestrator.py
cp llm_interface.py ./core/llm/llm_interface.py
cp ollama_provider.py ./core/llm/providers/ollama_provider.py

echo "  ✅ core/orchestrator.py"
echo "  ✅ core/llm/llm_interface.py"
echo "  ✅ core/llm/providers/ollama_provider.py"

# Atualiza .env com os novos modelos
if ! grep -q "DIOVAN_MODEL_FAST" .env 2>/dev/null; then
    echo "" >> .env
    echo "# Roteamento por níveis" >> .env
    echo "DIOVAN_MODEL_FAST=gemma2:2b" >> .env
    echo "DIOVAN_MODEL_NORMAL=llama3.2" >> .env
    echo "DIOVAN_MODEL_COMPLEX=diovan" >> .env
    echo "  ✅ .env atualizado com 3 níveis"
fi

# Mantém modelo carregado em memória
if ! grep -q "OLLAMA_KEEP_ALIVE" .env 2>/dev/null; then
    echo "OLLAMA_KEEP_ALIVE=-1" >> .env
    echo "  ✅ OLLAMA_KEEP_ALIVE=-1 adicionado"
fi

echo ""
echo "✅ Roteador instalado!"
echo ""
echo "Baixe o modelo rápido se ainda não tiver:"
echo "  ollama pull gemma2:2b"
echo ""
echo "Níveis configurados:"
echo "  ⚡ Nível 1 — gemma2:2b    (respostas simples)"
echo "  💡 Nível 2 — llama3.2     (uso geral)"
echo "  🧠 Nível 3 — diovan       (análises complexas)"
