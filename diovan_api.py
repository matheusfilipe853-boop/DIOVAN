"""
DIOVAN API — servidor HTTP local para integração com n8n.
Porta: 5680 (configurável via DIOVAN_API_PORT)

A interface estável entre o n8n (maestro) e o DIOVAN (motor). O n8n só fala
HTTP com esta API — nunca executa shell/Python diretamente.

Endpoints:
  GET  /health              → 200 {status, diovan_dir}
  GET  /status              → status agregado dos pipes (seen handles, playwright)
  GET  /status/{run_id}     → estado de um run específico (running|done|failed)
  GET  /runs                → histórico dos runs recentes
  POST /pipe   {"pipe": ...}        → dispara pipe (fire-and-forget), retorna {run_id, pid}
  POST /agent  {"message":}         → agente conversacional (Claude tool use)
  POST /search {"query","max_results"} → busca web DDGS (esteira de conteúdo LinkedIn)

Pipes aceitos: isp, mfs, ig, all, "all --parallel", status

Uso:
  python3 diovan_api.py
  make api-start
"""

import json
import os
import subprocess
import threading
import uuid
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from zoneinfo import ZoneInfo

DIOVAN_DIR = Path(__file__).parent
PORT       = int(os.getenv("DIOVAN_API_PORT", "5680"))
RUNS_DIR   = DIOVAN_DIR / "logs" / "api"
TZ         = ZoneInfo(os.getenv("DIOVAN_TZ", "America/Sao_Paulo"))

# Bases de pipe permitidas (a primeira palavra do comando)
ALLOWED_BASE = {"isp", "mfs", "ig", "all"}


def _load_env() -> None:
    """Carrega .env + .env.users/{user}/.env.user no ambiente do processo.
    Necessário para ANTHROPIC_API_KEY (agente) e demais segredos."""
    def _parse(path: Path, override: bool):
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k and (override or k not in os.environ):
                os.environ[k] = v.strip().strip('"').strip("'")

    _parse(DIOVAN_DIR / ".env", override=False)
    user_file = DIOVAN_DIR / ".diovan_user"
    user = user_file.read_text(encoding="utf-8").strip() if user_file.exists() else "default"
    _parse(DIOVAN_DIR / ".env.users" / user / ".env.user", override=True)
    # n8n/.env.n8n traz TELEGRAM_BOT_TOKEN/CHAT_ID e ANTHROPIC_API_KEY (sem sobrescrever)
    _parse(DIOVAN_DIR / "n8n" / ".env.n8n", override=False)


def _now() -> str:
    # Horário de Brasília com offset explícito (ex: 2026-05-31T17:15:16-03:00)
    return datetime.now(TZ).isoformat(timespec="seconds")


def _run_meta_path(run_id: str) -> Path:
    return RUNS_DIR / f"{run_id}.json"


def _write_meta(run_id: str, meta: dict) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    _run_meta_path(run_id).write_text(json.dumps(meta, ensure_ascii=False, indent=2))


def _read_meta(run_id: str) -> dict | None:
    p = _run_meta_path(run_id)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text())
    except Exception:
        return None


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ProcessLookupError):
        return False


def _status_snapshot() -> dict:
    """Status agregado via `bin/pipe status --json`."""
    try:
        out = subprocess.check_output(
            ["bash", str(DIOVAN_DIR / "bin" / "pipe"), "status", "--json"],
            cwd=str(DIOVAN_DIR),
            timeout=10,
            text=True,
        )
        return json.loads(out.strip())
    except Exception as e:
        return {"error": str(e)}


def _web_search(query: str, max_results: int = 5) -> dict:
    """Busca web genérica via DDGS (DuckDuckGo). Stateless.
    Usada pela esteira de conteúdo LinkedIn para enriquecer o tema."""
    try:
        from ddgs import DDGS
    except ImportError:
        return {"error": "ddgs não instalado (pip install ddgs)", "results": []}
    try:
        with DDGS() as ddgs:
            hits = list(ddgs.text(query, max_results=max(1, min(max_results, 15))))
        results = [
            {
                "title": h.get("title", ""),
                "body":  h.get("body", ""),
                "href":  h.get("href", ""),
            }
            for h in hits
        ]
        return {"query": query, "count": len(results), "results": results}
    except Exception as e:
        return {"error": str(e), "query": query, "results": []}


def _session_blocker(pipe: str) -> dict | None:
    """Circuit breaker preventivo: se o pipe depende da sessão Instagram e ela
    está ausente/expirada, NÃO dispara (evita run fadado + risco à conta).
    Retorna um dict de bloqueio, ou None se pode seguir."""
    base = pipe.split()[0]
    if base != "ig":  # só o ig depende 100% da sessão; mfs/all têm fallback interno
        return None

    sess = DIOVAN_DIR / ".env.users" / "playwright" / "session.json"
    if not sess.exists():
        stale = True
        motivo = "sessão Instagram ausente"
    else:
        age_h = (datetime.now(TZ).timestamp() - sess.stat().st_mtime) / 3600
        stale = age_h > 24
        motivo = f"sessão Instagram provavelmente expirada (há {int(age_h)}h)"

    if stale:
        return {
            "status": "blocked",
            "pipe": pipe,
            "reason": motivo,
            "action": "Rode `make ig-login` no terminal gráfico para reautenticar antes.",
        }
    return None


def _spawn_pipe(pipe: str) -> dict:
    """Dispara o pipe em background, registra metadata e acompanha o exit code."""
    blocked = _session_blocker(pipe)
    if blocked:
        return blocked

    run_id   = f"{datetime.now(TZ).strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
    log_path = RUNS_DIR / f"{run_id}.log"
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    log_fh = open(log_path, "w")
    child = subprocess.Popen(
        ["bash", str(DIOVAN_DIR / "bin" / "pipe"), *pipe.split()],
        cwd=str(DIOVAN_DIR),
        stdout=log_fh,
        stderr=subprocess.STDOUT,
    )

    meta = {
        "run_id"     : run_id,
        "pipe"       : pipe,
        "pid"        : child.pid,
        "status"     : "running",
        "started_at" : _now(),
        "finished_at": None,
        "exit_code"  : None,
        "log"        : str(log_path),
    }
    _write_meta(run_id, meta)

    def _watch():
        code = child.wait()
        log_fh.close()
        meta["status"]      = "done" if code == 0 else "failed"
        meta["exit_code"]   = code
        meta["finished_at"] = _now()
        _write_meta(run_id, meta)

    threading.Thread(target=_watch, daemon=True).start()
    return {"run_id": run_id, "pipe": pipe, "pid": child.pid, "status": "running"}


def _run_status(run_id: str) -> dict:
    meta = _read_meta(run_id)
    if meta is None:
        return {"error": f"run_id '{run_id}' não encontrado", "_code": 404}
    # Se a API reiniciou e perdeu a thread, reconcilia pelo PID
    if meta.get("status") == "running" and not _pid_alive(meta.get("pid", -1)):
        meta["status"] = "unknown"  # processo sumiu sem registrar exit code
    return meta


def _list_runs(limit: int = 20) -> dict:
    if not RUNS_DIR.exists():
        return {"runs": []}
    metas = []
    for p in sorted(RUNS_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True)[:limit]:
        try:
            m = json.loads(p.read_text())
            if m.get("status") == "running" and not _pid_alive(m.get("pid", -1)):
                m["status"] = "unknown"
            metas.append({k: m.get(k) for k in ("run_id", "pipe", "status", "started_at", "finished_at", "exit_code")})
        except Exception:
            continue
    return {"runs": metas}


def _agent_reply(message: str) -> dict:
    """Roda o agente conversacional local (Claude tool use)."""
    import diovan_agent
    executors = {
        "run_pipe":   lambda pipe: _spawn_pipe(pipe),
        "get_status": lambda: _status_snapshot(),
    }
    return diovan_agent.handle(message, executors)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[API] {self.address_string()} {fmt % args}")

    def _send(self, code: int, body: dict):
        body = dict(body)
        body.pop("_code", None)
        payload = json.dumps(body, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if self.path == "/health":
            self._send(200, {"status": "ok", "diovan_dir": str(DIOVAN_DIR)})
        elif self.path == "/status":
            self._send(200, _status_snapshot())
        elif self.path == "/runs":
            self._send(200, _list_runs())
        elif self.path.startswith("/status/"):
            run_id = self.path[len("/status/"):].strip("/")
            result = _run_status(run_id)
            self._send(result.get("_code", 200), result)
        else:
            self._send(404, {"error": "not found"})

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length) or b"{}")
        except Exception as e:
            self._send(400, {"error": f"invalid JSON: {e}"})
            return

        if self.path == "/agent":
            message = str(body.get("message", "")).strip()
            if not message:
                self._send(400, {"error": "campo 'message' obrigatório"})
                return
            self._send(200, _agent_reply(message))
            return

        if self.path == "/search":
            query = str(body.get("query", "")).strip()
            if not query:
                self._send(400, {"error": "campo 'query' obrigatório"})
                return
            max_results = body.get("max_results", 5)
            try:
                max_results = int(max_results)
            except (TypeError, ValueError):
                max_results = 5
            self._send(200, _web_search(query, max_results))
            return

        if self.path == "/pipe":
            pipe = str(body.get("pipe", "")).strip()
            if not pipe:
                self._send(400, {"error": "campo 'pipe' obrigatório"})
                return
            if pipe == "status":
                self._send(200, _status_snapshot())
                return
            base = pipe.split()[0]
            if base not in ALLOWED_BASE:
                self._send(400, {"error": f"pipe '{base}' inválido. Permitidos: {sorted(ALLOWED_BASE)}"})
                return
            self._send(200, _spawn_pipe(pipe))
            return

        self._send(404, {"error": "not found"})


if __name__ == "__main__":
    _load_env()

    # Bot Telegram (long-polling local) — sobe se houver token e agente
    if os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("ANTHROPIC_API_KEY"):
        import threading
        import diovan_bot
        threading.Thread(
            target=diovan_bot.poll_loop,
            args=(lambda msg: _agent_reply(msg),),
            daemon=True,
        ).start()

    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(f"[API] DIOVAN API rodando em http://127.0.0.1:{PORT}")
    print(f"[API] DIOVAN_DIR: {DIOVAN_DIR}")
    print(f"[API] Runs em: {RUNS_DIR}")
    print(f"[API] Agente: {'ON' if os.getenv('ANTHROPIC_API_KEY') else 'OFF (sem ANTHROPIC_API_KEY)'}")
    print(f"[API] Bot Telegram: {'ON' if os.getenv('TELEGRAM_BOT_TOKEN') and os.getenv('ANTHROPIC_API_KEY') else 'OFF'}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[API] Encerrado.")
