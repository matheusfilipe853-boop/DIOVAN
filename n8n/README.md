# DIOVAN + n8n

Automações e observabilidade dos pipes DIOVAN via n8n self-hosted.

## Arquitetura — quem faz o quê

O n8n é o **maestro** (orquestra, integra, agenda). O DIOVAN é o **motor**
(roda os pipes pesados). A fronteira é HTTP: o n8n **só** fala com a
`diovan_api.py` (porta 5680) e com APIs nativas — **nunca** executa shell/Python.

```
n8n (só HTTP)  ──►  diovan_api.py (5680)  ──►  bin/pipe  ──►  ISP · MFS · IG
```

**Regra de ouro:** nada de Code node com `child_process`/`$env` — o sandbox do
n8n 2.x bloqueia. Use sempre HTTP Request + nós nativos.

Por que os pipes não viram nós n8n: dependem de sessão Playwright que vive horas,
circuit breakers em memória e do BlockExecutor — tudo stateful, incompatível com
nós efêmeros. Então ficam em Python; o n8n dispara e acompanha via HTTP.

## Pré-requisito: subir a API DIOVAN

```bash
make api-start      # sobe diovan_api.py na porta 5680
curl -s http://127.0.0.1:5680/health
```

## Setup

```bash
# 1. Instalar e configurar n8n
make n8n-setup

# 2. Preencher credenciais
cp n8n/.env.n8n.example n8n/.env.n8n
# editar n8n/.env.n8n com:
#   TELEGRAM_BOT_TOKEN=  (obter com @BotFather no Telegram)
#   TELEGRAM_CHAT_ID=    (obter com @userinfobot)

# 3. Criar diretório de logs
mkdir -p logs/n8n

# 4. Iniciar n8n
make n8n-start

# 5. Acessar UI em http://localhost:5678
#    Usuário: diovan  |  Senha: diovan2026  (alterar em .env.n8n)
```

## Importar workflows

Na UI do n8n: **Settings → Import from file** → selecionar cada JSON de `n8n/workflows/`.

As três camadas:

**Camada 1 — Orquestração** (dispara pipes via API, notifica):
| Arquivo | Fluxo |
|---|---|
| `01_pipe_runner.json` | Cron diário 02:00 → `POST /pipe {all --parallel}` → Telegram c/ run_id |
| `02_overnight_controlled.json` | Liga IG 00:00, encerra 06:00 + notificação |
| `03_health_monitor.json` | `GET /status` a cada 30min, alerta se travado |
| `04_webhook_trigger.json` | `POST /webhook/diovan` → dispara pipe via API |

**Camada 2 — Integração de leads** (n8n no seu forte):
| Arquivo | Fluxo |
|---|---|
| `05_leads_integration.json` | Google Sheets (novos leads) → filtro → notifica/CRM |

**Camada 3 — Conteúdo LinkedIn** (esteira completa):
| Arquivo | Fluxo |
|---|---|
| `06_linkedin_content.json` | Sheets (ideias) → filtro → busca DDGS → Claude → publica → Sheets update |

### Esteira de LinkedIn — setup

**1. Planilha de ideias (Google Sheets)** — crie uma aba com este cabeçalho na linha 1:

| id | ideia | keywords_busca | status | data_para_post | post_id | data_publicada | post_gerado |
|----|-------|----------------|--------|----------------|---------|----------------|-------------|

- `ideia` — o briefing do post. `keywords_busca` — termos p/ enriquecer (opcional).
- `status` — deixe **vazio** para pendente; o fluxo grava `postado`.
- `data_para_post` — `YYYY-MM-DD`. O fluxo só pega linhas pendentes com data ≤ hoje.

**2. Pré-requisito: API DIOVAN no ar** (fornece o `/search` com DDGS):
```bash
make api-install && sudo systemctl enable --now diovan-api
curl -sX POST http://127.0.0.1:5680/search -H 'Content-Type: application/json' \
  -d '{"query":"gestão financeira personal trainer","max_results":3}'
```

**3. Credenciais no n8n** (UI → Credentials):
- **Google Sheets OAuth2** → conectar nos nós "Ler ideias" e "Marcar postado" + selecionar a planilha
- `ANTHROPIC_API_KEY` no `.env.n8n` (já está) — o nó Claude usa via `$env`

**4. Fluxo em duas fases:**

- **Fase 1 (agora, sem esperar o LinkedIn):** o último nó manda o post pronto pro
  **Telegram** para você revisar e publicar manual. Tudo o resto já roda e é testável.
- **Fase 2 (app LinkedIn aprovado):** troque o nó "Aprovação Telegram" por um nó
  **LinkedIn → Create Post** (credencial LinkedIn OAuth2) e adicione `post_id` no update.

> **Gargalo do LinkedIn:** a publicação automática exige um app no LinkedIn Developers
> com permissão `w_member_social`, que passa por review (dias a semanas). A Fase 1
> permite operar enquanto isso. Quando aprovar, é trocar um nó.

**Agente conversacional Telegram** — NÃO é workflow n8n, é bot Python local
(`diovan_bot.py` + `diovan_agent.py`). O Telegram Trigger do n8n exige webhook
HTTPS público, que o n8n local não tem; o bot resolve com long-polling nativo.

Sobe junto com a API (`make api-start`) se `TELEGRAM_BOT_TOKEN` + `ANTHROPIC_API_KEY`
estiverem disponíveis. Você fala em linguagem natural no Telegram e o agente
(Claude tool use) decide o que rodar / consulta status — tudo na máquina.

```
Você (Telegram):  bora buscar uns personal trainer
   → diovan_bot (long-polling) → diovan_agent (Claude) → run_pipe(ig) LOCAL
   → Telegram:  "Disparei o ig, run abc123."
```

Trava de segurança: só responde ao `TELEGRAM_CHAT_ID` configurado.

## Variáveis de ambiente

No `.env.n8n` (as expressões `{{ $env.X }}` nos HTTP Request nodes leem daqui):

| Variável | Usada por | Descrição |
|---|---|---|
| `DIOVAN_DIR` | todos | Caminho absoluto do projeto |
| `DIOVAN_API_URL` | 01–04 | `http://127.0.0.1:5680` |
| `TELEGRAM_BOT_TOKEN` | 01–06 | Token do bot (@BotFather) |
| `TELEGRAM_CHAT_ID` | 01–06 | ID do chat (@userinfobot) |
| `ANTHROPIC_API_KEY` | 06 | Claude API (esteira de conteúdo) |

## Configuração por workflow

- **05 (leads):** conecte uma credencial **Google Sheets OAuth** na UI e selecione
  a planilha de leads + aba no nó "Ler Leads". A ação default é notificar no
  Telegram — troque/some um nó HTTP para CRM, email ou WhatsApp.
- **06 (LinkedIn):** preencha `ANTHROPIC_API_KEY`. Gera o rascunho e envia pro
  Telegram para você revisar e publicar. Publicação automática no LinkedIn é
  fase 2 (requer LinkedIn API + OAuth de app aprovado + nó de aprovação com Wait).

## Webhook manual

```bash
# Acionar qualquer pipe via HTTP
curl -X POST http://localhost:5678/webhook/diovan \
     -H "Content-Type: application/json" \
     -d '{"pipe": "isp"}'

# Pipes válidos: isp, mfs, ig, all, status
```

## Atualizar workflows

1. Editar na UI do n8n
2. Exportar: **⋮ → Download**
3. Salvar em `n8n/workflows/` e commitar

## Service permanente (boot)

```bash
sudo systemctl enable diovan-n8n
sudo systemctl start diovan-n8n
sudo systemctl status diovan-n8n
```
