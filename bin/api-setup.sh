#!/bin/bash
# DIOVAN — instala a API (+ bot Telegram) como serviço systemd
# A API sobe o bot junto se TELEGRAM_BOT_TOKEN + ANTHROPIC_API_KEY existirem.
set -e

DIOVAN_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="$DIOVAN_DIR/venv/bin/python3"
UNIT="/etc/systemd/system/diovan-api.service"

echo "=== DIOVAN API — setup systemd ==="
echo "Diretório: $DIOVAN_DIR"

if [ ! -x "$PYTHON" ]; then
  echo "ERRO: $PYTHON não encontrado"
  exit 1
fi

mkdir -p "$DIOVAN_DIR/logs/api"

echo "Criando $UNIT (requer sudo)..."
sudo tee "$UNIT" > /dev/null << EOF
[Unit]
Description=DIOVAN API + Bot Telegram (motor de pipes)
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$DIOVAN_DIR
ExecStart=$PYTHON $DIOVAN_DIR/diovan_api.py
Restart=on-failure
RestartSec=10
StandardOutput=append:$DIOVAN_DIR/logs/api/api.log
StandardError=append:$DIOVAN_DIR/logs/api/api.log

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
echo "✓ Serviço criado."
echo ""
echo "Ativar no boot e iniciar agora:"
echo "  sudo systemctl enable --now diovan-api"
echo ""
echo "Comandos úteis:"
echo "  sudo systemctl status diovan-api      # estado"
echo "  sudo systemctl restart diovan-api     # reiniciar"
echo "  journalctl -u diovan-api -f           # logs ao vivo"
echo "  tail -f logs/api/api.log              # log do arquivo"
