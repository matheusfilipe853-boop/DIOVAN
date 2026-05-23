#!/bin/bash
set -e

echo "🖥️  Instalando interface do DIOVAN..."

# Estrutura de pastas
mkdir -p interface/adapters
touch interface/__init__.py
touch interface/adapters/__init__.py

# Arquivos de interface
cp base_interface.py interface/base_interface.py
cp terminal_adapter.py interface/adapters/terminal.py
cp interface_factory.py interface/interface_factory.py

echo "  ✅ interface/base_interface.py"
echo "  ✅ interface/adapters/terminal.py"
echo "  ✅ interface/interface_factory.py"

# Core files
cp main.py ./main.py
cp diovan.py ./diovan.py
cp Makefile ./Makefile

echo "  ✅ main.py"
echo "  ✅ diovan.py"
echo "  ✅ Makefile"

# Adiciona config no .env se não existir
if ! grep -q "DIOVAN_INTERFACE" .env 2>/dev/null; then
    echo "DIOVAN_INTERFACE=terminal" >> .env
    echo "  ✅ .env atualizado"
fi

echo ""
echo "✅ Interface instalada!"
echo ""
echo "Para iniciar o DIOVAN:"
echo "  make start"
echo ""
echo "O DIOVAN vai abrir automaticamente em um terminal externo."
