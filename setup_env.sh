#!/bin/bash

# ===========================================
# Setup do Ambiente Virtual - Projeto Jarvis
# ===========================================
# Execute dentro da pasta do projeto: cd diovan && ./setup_env.sh

set -e  # Para tudo se der erro

echo "🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado. Instale com: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "✅ $PYTHON_VERSION encontrado"

# ===========================================
# LIMPEZA: Remove pacotes globais desnecessários
# ===========================================
echo ""
echo "🧹 Limpando pacotes globais desnecessários..."

# Lista o que está instalado globalmente
echo "📦 Pacotes globais atuais:"
pip3 list --user 2>/dev/null || true

# Remove pacotes que devem ficar só no venv
PACKAGES_TO_CLEAN=("openai-whisper" "whisper" "requests" "python-dotenv")

for pkg in "${PACKAGES_TO_CLEAN[@]}"; do
    if pip3 show "$pkg" &> /dev/null 2>&1; then
        echo "  🗑️  Removendo $pkg do global..."
        pip3 uninstall "$pkg" -y 2>/dev/null || true
    fi
done

echo "✅ Limpeza concluída"

# ===========================================
# CRIAÇÃO DO AMBIENTE VIRTUAL
# ===========================================
echo ""
echo "📦 Criando ambiente virtual..."

if [ -d "venv" ]; then
    echo "⚠️  Pasta venv já existe. Removendo e recriando..."
    rm -rf venv
fi

python3 -m venv venv
echo "✅ Ambiente virtual criado em ./venv"

# Ativa o venv
source venv/bin/activate
echo "✅ Ambiente virtual ativado"

# ===========================================
# INSTALAÇÃO NA ORDEM CERTA
# ===========================================
echo ""
echo "📥 Instalando dependências na ordem correta..."

# 1. Atualiza pip primeiro (sempre)
echo ""
echo "1️⃣  Atualizando pip..."
pip install --upgrade pip

# 2. Ferramentas base
echo ""
echo "2️⃣  Instalando ferramentas base..."
pip install wheel setuptools

# 3. Dependências do sistema antes do Whisper
echo ""
echo "3️⃣  Instalando dependências numéricas..."
pip install numpy

# 4. PyTorch (necessário para Whisper rodar)
echo ""
echo "4️⃣  Instalando PyTorch (necessário para Whisper)..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# 5. Whisper (depois do PyTorch)
echo ""
echo "5️⃣  Instalando Whisper..."
pip install openai-whisper

# 6. Dependências do projeto
echo ""
echo "6️⃣  Instalando dependências do projeto..."
pip install requests python-dotenv

# 7. Opcional: PyAudio para captura de microfone
echo ""
echo "7️⃣  Instalando PyAudio para microfone..."
# Requer dependência do sistema primeiro
sudo apt-get install -y portaudio19-dev python3-pyaudio 2>/dev/null || echo "⚠️  PyAudio requer: sudo apt install portaudio19-dev"
pip install pyaudio 2>/dev/null || echo "⚠️  PyAudio não instalado, instale portaudio19-dev primeiro"

# ===========================================
# VERIFICAÇÃO FINAL
# ===========================================
echo ""
echo "🔍 Verificando instalações..."
echo ""

check_package() {
    if python -c "import $1" 2>/dev/null; then
        echo "  ✅ $1"
    else
        echo "  ❌ $1 - FALHOU"
    fi
}

check_package "whisper"
check_package "torch"
check_package "requests"
check_package "dotenv"

# ===========================================
# GERA requirements.txt com versões exatas
# ===========================================
echo ""
echo "📝 Gerando requirements.txt com versões instaladas..."
pip freeze > requirements.txt
echo "✅ requirements.txt atualizado"

# ===========================================
# INSTRUÇÕES FINAIS
# ===========================================
echo ""
echo "================================================"
echo "✅ Ambiente configurado com sucesso!"
echo "================================================"
echo ""
echo "Para ativar o ambiente sempre que for trabalhar:"
echo "  source venv/bin/activate"
echo ""
echo "Para desativar:"
echo "  deactivate"
echo ""
echo "Para rodar o projeto:"
echo "  source venv/bin/activate && python main.py"
echo ""
