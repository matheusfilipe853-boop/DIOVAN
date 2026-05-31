"""
DIOVAN Bot — long-polling do Telegram, 100% local.

Substitui o Telegram Trigger do n8n (que exige webhook HTTPS público).
Faz getUpdates direto na API do Telegram, roteia cada mensagem para o
agente local (diovan_agent via /agent) e responde. Sem HTTPS, sem túnel.

Sobe automaticamente junto com a diovan_api.py se TELEGRAM_BOT_TOKEN existir.
"""

import json
import os
import time
import urllib.request
import urllib.parse


def _tg(token: str, method: str, params: dict, timeout: int = 70) -> dict:
    url  = f"https://api.telegram.org/bot{token}/{method}"
    data = urllib.parse.urlencode(params).encode()
    req  = urllib.request.Request(url, data=data)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def send_message(token: str, chat_id, text: str) -> None:
    try:
        _tg(token, "sendMessage", {"chat_id": chat_id, "text": text}, timeout=20)
    except Exception as e:
        print(f"[BOT] falha ao enviar: {e}")


def poll_loop(agent_fn, token: str | None = None, allowed_chat: str | None = None) -> None:
    """
    agent_fn(message:str) -> {"reply": str, ...}
    allowed_chat: se definido, só responde a esse chat_id (trava de segurança).
    """
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("[BOT] TELEGRAM_BOT_TOKEN ausente — bot desativado")
        return
    allowed_chat = str(allowed_chat or os.getenv("TELEGRAM_CHAT_ID") or "").strip()

    # getUpdates não funciona com webhook ativo — garante que está limpo
    try:
        _tg(token, "deleteWebhook", {"drop_pending_updates": "false"}, timeout=15)
    except Exception:
        pass

    print(f"[BOT] Long-polling Telegram iniciado (trava de chat: {'sim' if allowed_chat else 'NÃO'})")
    offset = None
    while True:
        try:
            params = {"timeout": 60}
            if offset is not None:
                params["offset"] = offset
            resp = _tg(token, "getUpdates", params)

            for upd in resp.get("result", []):
                offset = upd["update_id"] + 1
                msg     = upd.get("message") or {}
                text    = (msg.get("text") or "").strip()
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if not text:
                    continue
                if allowed_chat and chat_id != allowed_chat:
                    print(f"[BOT] mensagem de chat não autorizado ({chat_id}) ignorada")
                    continue

                print(f"[BOT] ◀ {text[:60]}")
                try:
                    result = agent_fn(text)
                    reply  = result.get("reply", "(sem resposta)")
                except Exception as e:
                    reply = f"⚠️ erro no agente: {e}"
                send_message(token, chat_id, reply)
                print(f"[BOT] ▶ {reply[:60]}")

        except Exception as e:
            print(f"[BOT] erro no loop: {e} — retry em 5s")
            time.sleep(5)
