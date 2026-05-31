#!/bin/bash
# DIOVAN — Setup do n8n
# Instala n8n via npm e configura serviço systemd
set -e

DIOVAN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
N8N_DIR="$DIOVAN_DIR/n8n"
USER_HOME="$HOME"

echo "=== DIOVAN n8n Setup ==="
echo "Diretório DIOVAN: $DIOVAN_DIR"
echo ""

# ── Verifica node ──────────────────────────────────────────
if ! command -v node &>/dev/null; then
  echo "ERRO: Node.js não encontrado. Instale com:"
  echo "  curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -"
  echo "  sudo apt-get install -y nodejs"
  exit 1
fi
echo "✓ Node $(node --version)"

# ── Instala n8n ────────────────────────────────────────────
if ! command -v n8n &>/dev/null; then
  echo "Instalando n8n..."
  npm install -g n8n
  echo "✓ n8n instalado"
else
  echo "✓ n8n $(n8n --version) já instalado"
fi

# ── Cria .env.n8n se não existe ────────────────────────────
ENV_FILE="$N8N_DIR/.env.n8n"
if [ ! -f "$ENV_FILE" ]; then
  cp "$N8N_DIR/.env.n8n.example" "$ENV_FILE"
  echo "✓ Criado $ENV_FILE — edite com suas credenciais Telegram"
else
  echo "✓ $ENV_FILE já existe"
fi

# ── Cria serviço systemd ───────────────────────────────────
UNIT_FILE="/etc/systemd/system/diovan-n8n.service"
if [ ! -f "$UNIT_FILE" ]; then
  echo "Criando serviço systemd (requer sudo)..."
  sudo tee "$UNIT_FILE" > /dev/null << EOF
[Unit]
Description=n8n — DIOVAN Automation
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DIOVAN_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$(which n8n) start
Restart=on-failure
RestartSec=10
StandardOutput=append:$DIOVAN_DIR/logs/n8n/n8n.log
StandardError=append:$DIOVAN_DIR/logs/n8n/n8n.log

[Install]
WantedBy=multi-user.target
EOF
  sudo systemctl daemon-reload
  echo "✓ Serviço systemd criado"
  echo ""
  echo "Para iniciar automaticamente no boot:"
  echo "  sudo systemctl enable diovan-n8n"
  echo "  sudo systemctl start diovan-n8n"
else
  echo "✓ Serviço systemd já existe"
fi

echo ""
echo "=== Próximos passos ==="
echo ""
echo "1. Edite n8n/.env.n8n com seus dados:"
echo "   TELEGRAM_BOT_TOKEN=  seu token do @BotFather"
echo "   TELEGRAM_CHAT_ID=    seu chat ID"
echo ""
echo "2. Inicie o n8n:"
echo "   make n8n-start"
echo ""
echo "3. Acesse http://localhost:5678"
echo ""
echo "4. Importe os workflows de n8n/workflows/ via Settings → Import"
