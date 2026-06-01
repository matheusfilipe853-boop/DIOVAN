"""
DIOVAN — Reautenticação Instagram (manual, com tela).

Abre o Chrome VISÍVEL para você logar no Instagram (login + 2FA se pedir) e
salva a sessão em .env.users/playwright/session.json. A partir daí os runs
do pipe ig rodam headless e podem ser comandados pelo Telegram.

Rode no SEU terminal gráfico (não via systemd/Telegram — precisa de tela):
    make ig-login
"""

import os
import sys
from pathlib import Path

DIOVAN_DIR = Path(__file__).parent


def _load_env():
    for path, override in [(DIOVAN_DIR / ".env", False),
                           (DIOVAN_DIR / "n8n" / ".env.n8n", False)]:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            if k and (override or k not in os.environ):
                os.environ[k] = v.strip().strip('"').strip("'")
    # .env.user do usuário ativo
    uf = DIOVAN_DIR / ".diovan_user"
    user = uf.read_text().strip() if uf.exists() else "default"
    p = DIOVAN_DIR / ".env.users" / user / ".env.user"
    if p.exists():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip('"').strip("'")


def main() -> int:
    if not os.getenv("DISPLAY") and not os.getenv("WAYLAND_DISPLAY"):
        print("✗ Sem tela (DISPLAY/WAYLAND ausente). Rode num terminal gráfico.")
        return 2

    _load_env()
    user = os.getenv("INSTAGRAM_USER") or os.getenv("IG_USERNAME", "")
    pwd  = os.getenv("INSTAGRAM_PASS") or os.getenv("IG_PASSWORD", "")
    if not user or not pwd:
        print("✗ INSTAGRAM_USER / INSTAGRAM_PASS ausentes no .env")
        return 2

    from playwright.sync_api import sync_playwright
    from executors.instagram.profile_fetcher import (
        get_cached_session, close_cached_session, SESSION_PATH,
    )

    # força nova captura: remove a sessão velha
    SESSION_PATH.unlink(missing_ok=True)
    print(f"  Reautenticando @{user} — o Chrome vai abrir para o login...")
    print("  Faça login (e 2FA se pedir). A sessão será salva ao final.\n")

    try:
        get_cached_session(sync_playwright, user, pwd)
        ok = SESSION_PATH.exists()
        close_cached_session()
        if ok:
            print(f"\n✓ Sessão salva em {SESSION_PATH}")
            print("  Agora você pode comandar o pipe ig pelo Telegram.")
            return 0
        print("\n✗ Sessão não foi salva. Tente de novo.")
        return 1
    except Exception as e:
        print(f"\n✗ Falha na reautenticação: {e}")
        close_cached_session()
        return 1


if __name__ == "__main__":
    sys.exit(main())
