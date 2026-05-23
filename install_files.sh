#!/bin/bash

# ===========================================
# Instala arquivos do ZIP nas pastas corretas
# ===========================================
# Execute dentro da pasta diovan:
# chmod +x install_files.sh && ./install_files.sh

ZIP_PATH="$HOME/Downloads/files.zip"
TMP_DIR="/tmp/diovan_files"

# Verifica se o ZIP existe
if [ ! -f "$ZIP_PATH" ]; then
    echo "❌ Arquivo não encontrado em: $ZIP_PATH"
    echo "   Verifique se o nome do arquivo está correto."
    exit 1
fi

echo "📦 Extraindo arquivos..."
rm -rf "$TMP_DIR"
mkdir -p "$TMP_DIR"
unzip -o "$ZIP_PATH" -d "$TMP_DIR"

echo ""
echo "📁 Copiando para as pastas corretas..."

# main.py → raiz do projeto
if [ -f "$TMP_DIR/main.py" ]; then
    cp "$TMP_DIR/main.py" ./main.py
    echo "  ✅ main.py → diovan/main.py"
fi

# orchestrator.py → core/
if [ -f "$TMP_DIR/orchestrator.py" ]; then
    cp "$TMP_DIR/orchestrator.py" ./core/orchestrator.py
    echo "  ✅ orchestrator.py → diovan/core/orchestrator.py"
fi

# llm_interface.py → core/llm/
if [ -f "$TMP_DIR/llm_interface.py" ]; then
    cp "$TMP_DIR/llm_interface.py" ./core/llm/llm_interface.py
    echo "  ✅ llm_interface.py → diovan/core/llm/llm_interface.py"
fi

# ollama_provider.py → core/llm/providers/
if [ -f "$TMP_DIR/ollama_provider.py" ]; then
    cp "$TMP_DIR/ollama_provider.py" ./core/llm/providers/ollama_provider.py
    echo "  ✅ ollama_provider.py → diovan/core/llm/providers/ollama_provider.py"
fi

# Limpeza
rm -rf "$TMP_DIR"

echo ""
echo "✅ Todos os arquivos instalados com sucesso!"
echo ""
echo "Para rodar o assistente:"
echo "  source venv/bin/activate && python3 main.py"
