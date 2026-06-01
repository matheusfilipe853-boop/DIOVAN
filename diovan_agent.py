"""
DIOVAN Agent — operador conversacional dos pipes via Claude (tool use).

Roda LOCAL, dentro da diovan_api.py. O n8n só transporta a mensagem do
Telegram até aqui e devolve o reply. A inteligência (decidir o que rodar,
consultar status) fica na máquina — o pesado nunca sai do local.

Uso:
    from diovan_agent import handle
    result = handle("bora buscar uns personal trainer", executors)
    # → {"reply": "Disparando o pipe ig...", "actions": [...]}
"""

import json
import os

# Haiku dá conta: escopo fechado (interpretar comando → run_pipe/get_status).
# Override via DIOVAN_AGENT_MODEL se precisar de mais capacidade.
MODEL = os.getenv("DIOVAN_AGENT_MODEL", "claude-haiku-4-5-20251001")

SYSTEM = """Você é o operador do DIOVAN — o sistema de prospecção do Matheus — falando pelo Telegram.

Os pipes disponíveis:
- isp: prospecção de provedores de internet regionais (Anatel + enriquecimento CNPJ)
- mfs: prospecção via comentários do YouTube (personal trainers que demonstram dor de gestão)
- ig: prospecção de personal trainers via busca no Instagram (DDGS + Playwright)
- all: roda os três em paralelo

Regras:
- Responda SEMPRE em português brasileiro, direto e curto (é Telegram).
- Horários estão em Brasília (-03:00). Ao citar horas, use o horário local sem o sufixo de fuso.
- Quando o Matheus pedir para rodar/buscar/prospectar algo, use a ferramenta run_pipe.
- Quando perguntar como está, progresso, status, quantos leads — use get_status.
- Não invente números. Se não tiver o dado, use get_status para buscar.
- Sem formalidade excessiva. Fale como um operador parceiro, não um assistente corporativo.
- Confirme a ação que tomou em uma frase (ex: "Disparei o ig, run abc123").

Como LER o get_status (não exagere nem invente):
- playwright_session "salva" só significa que existe um arquivo de sessão. Se
  playwright_stale=true, a sessão está velha e PROVAVELMENTE EXPIRADA — avise isso,
  não diga que está "ativa" nem que está rodando.
- handles_vistos é dedup histórico da busca — NÃO são leads salvos na planilha nem
  vendas. Nunca apresente como progresso de leads. É só quantos perfis já foram
  processados para não repetir.
- ultimo_run mostra a última execução real. Se for "nenhum run registrado", então
  NADA rodou ainda nesta instalação — seja honesto sobre isso.
- Se não houve run e a sessão está stale, diga claramente: não há atividade recente
  e talvez precise reautenticar antes de rodar.

Se run_pipe retornar status "blocked": a sessão Instagram está expirada/ausente e o
sistema NÃO disparou (de propósito, pra não falhar nem arriscar a conta). Repasse o
motivo e diga ao Matheus para rodar `make ig-login` no terminal com tela. Não insista
em disparar — o login do Instagram exige tela e interação humana (2FA), não dá pra
fazer pelo Telegram."""

TOOLS = [
    {
        "name": "run_pipe",
        "description": (
            "Dispara um pipe de prospecção do DIOVAN na máquina local. "
            "isp = provedores de internet regionais; mfs = comentários do YouTube; "
            "ig = personal trainers via Instagram; all = todos em paralelo. "
            "Retorna run_id para acompanhamento posterior."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "pipe": {"type": "string", "enum": ["isp", "mfs", "ig", "all"]}
            },
            "required": ["pipe"],
        },
    },
    {
        "name": "get_status",
        "description": (
            "Consulta o estado atual do DIOVAN: handles/leads já vistos, "
            "se a sessão Playwright está ativa, último log. Use para responder "
            "perguntas sobre progresso, status ou 'como está indo'."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]


def handle(message: str, executors: dict, history: list | None = None) -> dict:
    """
    Processa uma mensagem em linguagem natural, deixando o Claude decidir
    quais ferramentas chamar. `executors` mapeia nome da tool → callable.
    Retorna {"reply": str, "actions": [...]}.
    """
    from anthropic import Anthropic

    if not os.getenv("ANTHROPIC_API_KEY"):
        return {"reply": "⚠️ ANTHROPIC_API_KEY não configurada na máquina.", "actions": []}

    client   = Anthropic()
    messages = list(history or [])
    messages.append({"role": "user", "content": message})
    actions  = []

    for _ in range(6):  # teto de iterações de tool use
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=[{"type": "text", "text": SYSTEM, "cache_control": {"type": "ephemeral"}}],
            tools=TOOLS,
            messages=messages,
        )

        if resp.stop_reason != "tool_use":
            reply = "".join(b.text for b in resp.content if b.type == "text").strip()
            return {"reply": reply or "(sem resposta)", "actions": actions}

        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            fn = executors.get(block.name)
            if fn is None:
                out = {"error": f"ferramenta '{block.name}' indisponível"}
            else:
                try:
                    out = fn(**block.input) if block.input else fn()
                except Exception as e:
                    out = {"error": str(e)}
            actions.append({"tool": block.name, "input": block.input, "output": out})
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(out, ensure_ascii=False),
            })
        messages.append({"role": "user", "content": results})

    return {"reply": "(atingi o limite de passos sem concluir)", "actions": actions}
