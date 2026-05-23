#!/bin/bash
set -e

echo "🔊 Instalando TTS adapter do DIOVAN..."

# Cria pasta de assets
mkdir -p assets/voice

# Copia o adapter
cp tts_adapter.py interface/adapters/tts.py
echo "  ✅ interface/adapters/tts.py"

# Copia o script de teste
cp test_tts.py test_tts.py
echo "  ✅ test_tts.py"

# Verifica se o arquivo de voz existe
if [ -f "assets/voice/VOZDIOVAN.mp3" ]; then
    echo "  ✅ assets/voice/VOZDIOVAN.mp3 encontrado"
else
    echo "  ⚠️  Coloque o arquivo VOZDIOVAN.mp3 em assets/voice/"
fi

echo ""
echo "✅ TTS instalado!"
echo ""
echo "Para testar:"
echo "  source venv/bin/activate && python3 test_tts.py"
