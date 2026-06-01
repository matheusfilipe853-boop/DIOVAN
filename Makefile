SHELL := /bin/bash

start:
	ollama serve & source venv/bin/activate && python3 main.py

diovan:
	source venv/bin/activate && python3 diovan.py

overnight:
	@mkdir -p logs/overnight
	source venv/bin/activate && \
	OAUTHLIB_RELAX_TOKEN_SCOPE=1 python3 -m packages.run_overnight $(ARGS) \
	  2>&1 | tee logs/overnight/$$(date +%Y-%m-%d_%H-%M).log

stop:
	pkill ollama

api-start:
	@mkdir -p logs/api
	venv/bin/python3 diovan_api.py

api-stop:
	@pkill -f "diovan_api.py" 2>/dev/null && echo "API encerrada" || echo "API não estava rodando"

api-install:
	bash bin/api-setup.sh

ig-login:
	venv/bin/python3 ig_login.py

api-logs:
	@journalctl -u diovan-api -f 2>/dev/null || tail -f logs/api/api.log

n8n-setup:
	bash n8n/setup.sh

n8n-start:
	@mkdir -p logs/n8n n8n/data
	@[ -f n8n/.env.n8n ] || (echo "ERRO: copie n8n/.env.n8n.example para n8n/.env.n8n e preencha" && exit 1)
	@if ss -tlnp 2>/dev/null | grep -q :5678; then \
		echo "n8n já está rodando em http://localhost:5678"; \
	else \
		set -a && . n8n/.env.n8n && set +a && n8n start; \
	fi

n8n-restart:
	@pkill -f "n8n start" 2>/dev/null || true
	@sleep 1
	@mkdir -p logs/n8n n8n/data
	set -a && . n8n/.env.n8n && set +a && n8n start

n8n-stop:
	@pkill -f "n8n start" 2>/dev/null && echo "n8n encerrado" || echo "n8n não estava rodando"
