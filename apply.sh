#!/bin/bash

# ===========================================
# DIOVAN — Script de aplicação da sessão
# Execute dentro da pasta diovan/:
#   chmod +x apply.sh && ./apply.sh
# ===========================================

set -e

echo "🧠 Aplicando arquivos da sessão DIOVAN..."
echo ""

# --- DOCUMENTAÇÃO ---
echo "📄 Documentação..."
cp DIOVAN_VISION.md ./DIOVAN_VISION.md
cp DIOVAN_ROADMAP.md ./DIOVAN_ROADMAP.md
echo "  ✅ DIOVAN_VISION.md"
echo "  ✅ DIOVAN_ROADMAP.md"

# --- MODELFILES ---
echo ""
echo "🧬 Modelfiles..."
cp Modelfile ./Modelfile
cp Userfile ./Userfile
cp Modelfile.combined ./Modelfile.combined
echo "  ✅ Modelfile"
echo "  ✅ Userfile"
echo "  ✅ Modelfile.combined"

# --- CÓDIGO FONTE ---
echo ""
echo "⚙️  Código fonte..."
cp main.py ./main.py
cp orchestrator.py ./core/orchestrator.py
cp llm_interface.py ./core/llm/llm_interface.py
cp ollama_provider.py ./core/llm/providers/ollama_provider.py
cp github_executor.py ./executors/github/github_executor.py
echo "  ✅ main.py"
echo "  ✅ core/orchestrator.py"
echo "  ✅ core/llm/llm_interface.py"
echo "  ✅ core/llm/providers/ollama_provider.py"
echo "  ✅ executors/github/github_executor.py"

# --- REGISTRAR DIOVAN NO OLLAMA ---
echo ""
echo "🤖 Registrando DIOVAN no Ollama..."
if command -v ollama &> /dev/null; then
    ollama pull mistral
    ollama create diovan -f Modelfile.combined
    echo "  ✅ DIOVAN registrado. Teste com: ollama run diovan"
else
    echo "  ⚠️  Ollama não encontrado. Instale e rode manualmente:"
    echo "      ollama pull mistral"
    echo "      ollama create diovan -f Modelfile.combined"
fi

# --- PRÓXIMOS PASSOS ---
echo ""
echo "================================================"
echo "✅ Sessão aplicada com sucesso!"
echo "================================================"
echo ""
echo "PRÓXIMOS PASSOS:"
echo ""
echo "1. Inicie o DIOVAN:"
echo "   make start"
echo ""
echo "2. Teste a identidade:"
echo "   Você: Quem é você?"
echo ""
echo "3. Teste o GitHub sem alucinação:"
echo "   Você: Como está implementado o OAuth Google no projeto?"
echo ""
echo "4. Leia o roadmap do dia:"
echo "   cat DIOVAN_ROADMAP.md"
echo ""
