"""
DIOVAN — Pacote google_auth
Skill: AUTH_GOOGLE
Autentica usuário via OAuth Google.
Salva token em .env.users/{user_id}/google_token.json
Renova automaticamente quando expirado.

Dependências: nenhuma
Env pública: .env.public.google.json (credenciais OAuth)
Env usuário: .env.users/{email}/google_token.json
"""

import os
import json
from pathlib import Path
from core.package_loader import Package, Skill

# ─────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────

CREDENTIALS_FILE = Path(".env.public.google.json")
USERS_DIR        = Path(".env.users")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "openid",
    "email",
    "profile",
]

# ─────────────────────────────────────────
# TOKEN MANAGER
# ─────────────────────────────────────────

def _get_token_path(user_id: str) -> Path:
    path = USERS_DIR / user_id
    path.mkdir(parents=True, exist_ok=True)
    return path / "google_token.json"

def _save_token(user_id: str, creds):
    token_path = _get_token_path(user_id)
    token_data = {
        "token"        : creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri"    : creds.token_uri,
        "client_id"    : creds.client_id,
        "client_secret": creds.client_secret,
        "scopes"       : list(creds.scopes) if creds.scopes else SCOPES,
        "email"        : user_id,
    }
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)
    # Protege o arquivo
    os.chmod(token_path, 0o600)

def _load_token(user_id: str):
    """Carrega token salvo. Retorna None se não existir."""
    try:
        from google.oauth2.credentials import Credentials
        token_path = _get_token_path(user_id)
        if not token_path.exists():
            return None
        with open(token_path) as f:
            data = json.load(f)
        return Credentials(
            token         = data["token"],
            refresh_token = data["refresh_token"],
            token_uri     = data["token_uri"],
            client_id     = data["client_id"],
            client_secret = data["client_secret"],
            scopes        = data["scopes"],
        )
    except Exception:
        return None

def _get_user_email(creds) -> str:
    """Obtém email do usuário autenticado"""
    try:
        import requests
        response = requests.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {creds.token}"}
        )
        return response.json().get("email", "unknown")
    except Exception:
        return "unknown"

# ─────────────────────────────────────────
# SKILL HANDLER
# ─────────────────────────────────────────

def auth_google_handler(context: dict) -> dict:
    """
    Autentica usuário via OAuth Google.
    Usa token salvo se válido, renova se expirado,
    ou abre browser para novo login.
    """
    try:
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request

        if not CREDENTIALS_FILE.exists():
            return {
                "success": False,
                "error"  : f"Credenciais não encontradas: {CREDENTIALS_FILE}"
            }

        # Tenta carregar token do usuário atual
        user_id = context.get("user_id", "default")
        creds   = _load_token(user_id)

        # Verifica se precisa renovar
        if creds and creds.expired and creds.refresh_token:
            print("  Renovando token Google...")
            creds.refresh(Request())
            email = _get_user_email(creds)
            _save_token(email, creds)
            return {
                "success"   : True,
                "token"     : creds.token,
                "email"     : email,
                "renovado"  : True,
                "creds"     : creds,
            }

        # Token válido existente
        if creds and creds.valid:
            email = _get_user_email(creds)
            return {
                "success" : True,
                "token"   : creds.token,
                "email"   : email,
                "renovado": False,
                "creds"   : creds,
            }

        # Novo login via browser
        print("  Abrindo browser para autenticação Google...")
        flow = InstalledAppFlow.from_client_secrets_file(
            CREDENTIALS_FILE,
            scopes      = SCOPES,
            redirect_uri= "urn:ietf:wg:oauth:2.0:oob"
        )

        creds = flow.run_local_server(
            port              = 0,
            access_type       = "offline",
            include_granted_scopes = "true"
        )

        # Obtém email e salva token
        email = _get_user_email(creds)
        _save_token(email, creds)

        print(f"  Autenticado como: {email}")

        return {
            "success"   : True,
            "token"     : creds.token,
            "email"     : email,
            "novo_login": True,
            "creds"     : creds,
        }

    except ImportError:
        return {
            "success": False,
            "error"  : "Instale: pip install google-auth google-auth-oauthlib google-auth-httplib2"
        }
    except Exception as e:
        return {
            "success": False,
            "error"  : str(e)
        }

# ─────────────────────────────────────────
# FACTORY — cria o pacote pronto para carregar
# ─────────────────────────────────────────

def create_package() -> Package:
    """Cria e retorna o pacote google_auth"""
    pkg = Package(
        name         = "google_auth",
        package_type = 0,           # ACAO
        version      = "1.0.0",
        author       = "Matheus F. Souza",
        dependencies = [],          # sem dependências
    )

    pkg.register_skill(Skill(
        name          = "AUTH_GOOGLE",
        handler       = auth_google_handler,
        risk          = "LOW",
        input_schema  = {"user_id": "str (opcional)"},
        output_schema = {
            "success": "bool",
            "token"  : "str",
            "email"  : "str",
            "creds"  : "Credentials",
        }
    ))

    return pkg


# ─────────────────────────────────────────
# TESTE DIRETO
# ─────────────────────────────────────────

if __name__ == "__main__":
    from core.nucleus import get_nucleus
    from core.package_loader import PackageLoader
    from core.block_executor import BlockExecutor, ExecutionBlock, Instruction

    print("Testando google_auth\n")

    nucleus = get_nucleus()
    loader  = PackageLoader(nucleus)
    pkg     = create_package()
    loader.load_python_package(pkg)

    print(f"Pacote: {pkg}")
    print(f"Skills: {pkg.skills}\n")

    block = ExecutionBlock("Autenticar com Google")
    block.add(Instruction("AUTH_GOOGLE", risk="LOW"))

    executor = BlockExecutor()
    result   = executor.execute(block)

    print(f"\nResultado:")
    auth = result.get("AUTH_GOOGLE", {})
    if auth.get("success"):
        print(f"  Email: {auth.get('email')}")
        print(f"  Token: {auth.get('token', '')[:20]}...")
        print(f"  Novo login: {auth.get('novo_login', False)}")
    else:
        print(f"  Erro: {auth.get('error')}")
