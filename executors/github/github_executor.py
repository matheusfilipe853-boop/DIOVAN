"""
Executor GitHub - consulta repositório via API REST.
Não clona nada localmente, tudo via requisições HTTP.
Requer GITHUB_TOKEN e GITHUB_REPO no .env
"""

import requests
import base64
import os
import concurrent.futures
from datetime import datetime, timedelta
from dotenv import load_dotenv
from executors.base_executor import BaseExecutor
from config.runtime import GITHUB_TIMEOUT

load_dotenv()

class GitHubExecutor(BaseExecutor):
    def __init__(self):
        self.token    = os.getenv("GITHUB_TOKEN")
        self.repo     = os.getenv("GITHUB_REPO")
        self.base_url = "https://api.github.com"
        self.headers  = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def execute(self, command: dict) -> dict:
        action = command.get("action")
        params = command.get("params", {})

        actions = {
            "recent_commits"  : self._recent_commits,
            "open_issues"     : self._open_issues,
            "pull_requests"   : self._pull_requests,
            "repo_summary"    : self._repo_summary,
            "file_structure"  : self._file_structure,
            "deployments"     : self._deployments,
            "weekly_activity" : self._weekly_activity,
            "search_file"     : self._search_file,
            "read_file"       : self._read_file,
        }

        if action not in actions:
            return {"success": False, "output": f"Ação desconhecida: {action}"}

        return actions[action](params)

    def _search_file(self, params: dict) -> dict:
        query = params.get("query", "")
        if not query:
            return {"success": False, "output": "Nenhum termo de busca fornecido"}

        response = self._get(
            "/search/code",
            {"q": f"{query} repo:{self.repo}", "per_page": 5}
        )

        if not response or not response.get("items"):
            return {"success": False, "output": f"Nenhum arquivo encontrado para: {query}"}

        results = []
        summary = f"🔎 Arquivos encontrados para '{query}':\n"

        for item in response["items"]:
            summary += f"  📄 {item['path']}\n"
            results.append(item["path"])

        code_extensions = ['.ts', '.tsx', '.py', '.js', '.jsx']

        best_match = (
            next((r for r in results if 'auth' in r.lower() and any(r.endswith(ext) for ext in code_extensions)), None)
            or next((r for r in results if any(r.endswith(ext) for ext in code_extensions)), None)
            or results[0]
        )

        content_result = self._read_file({"path": best_match})

        if content_result["success"]:
            summary += f"\n📖 Conteúdo de {best_match}:\n"
            summary += "```\n"
            summary += content_result["output"][:1500]
            summary += "\n```"

        return {"success": True, "output": summary, "data": results}

    def _read_file(self, params: dict) -> dict:
        path = params.get("path", "")
        if not path:
            return {"success": False, "output": "Caminho do arquivo não fornecido"}

        response = self._get(f"/repos/{self.repo}/contents/{path}")

        if not response:
            return {"success": False, "output": f"Arquivo não encontrado: {path}"}

        try:
            content = base64.b64decode(response["content"]).decode("utf-8")
            return {"success": True, "output": content, "data": {"path": path, "size": response["size"]}}
        except Exception as e:
            return {"success": False, "output": f"Erro ao decodificar arquivo: {e}"}

    def _recent_commits(self, params: dict) -> dict:
        days  = params.get("days", 7)
        since = (datetime.utcnow() - timedelta(days=days)).isoformat() + "Z"

        response = self._get(f"/repos/{self.repo}/commits", {"since": since, "per_page": 20})
        if not response:
            return {"success": False, "output": "Erro ao buscar commits"}

        commits = []
        for c in response:
            commits.append({
                "sha"    : c["sha"][:7],
                "message": c["commit"]["message"].split("\n")[0],
                "author" : c["commit"]["author"]["name"],
                "date"   : c["commit"]["author"]["date"][:10]
            })

        summary = f"📋 Últimos commits ({days} dias):\n"
        for c in commits:
            summary += f"  [{c['sha']}] {c['date']} - {c['author']}: {c['message']}\n"

        return {"success": True, "output": summary, "data": commits}

    def _open_issues(self, params: dict) -> dict:
        response = self._get(f"/repos/{self.repo}/issues", {"state": "open", "per_page": 20})
        if response is None:
            return {"success": False, "output": "Erro ao buscar issues"}

        if not response:
            return {"success": True, "output": "✅ Nenhuma issue aberta no momento."}

        summary = f"🐛 Issues abertas ({len(response)}):\n"
        for issue in response:
            labels    = ", ".join([l["name"] for l in issue.get("labels", [])])
            label_str = f" [{labels}]" if labels else ""
            summary  += f"  #{issue['number']}{label_str} - {issue['title']}\n"

        return {"success": True, "output": summary, "data": response}

    def _pull_requests(self, params: dict) -> dict:
        state    = params.get("state", "open")
        response = self._get(f"/repos/{self.repo}/pulls", {"state": state, "per_page": 10})
        if response is None:
            return {"success": False, "output": "Erro ao buscar pull requests"}

        if not response:
            return {"success": True, "output": f"Nenhum PR {state} no momento."}

        summary = f"🔀 Pull Requests ({state}) - {len(response)} encontrados:\n"
        for pr in response:
            summary += f"  #{pr['number']} - {pr['title']} ({pr['user']['login']})\n"

        return {"success": True, "output": summary, "data": response}

    def _repo_summary(self, params: dict) -> dict:
        response = self._get(f"/repos/{self.repo}")
        if not response:
            return {"success": False, "output": "Erro ao buscar dados do repositório"}

        summary = f"""
📦 Repositório: {response['full_name']}
📝 Descrição: {response.get('description', 'Sem descrição')}
⭐ Stars: {response['stargazers_count']}
🍴 Forks: {response['forks_count']}
🐛 Issues abertas: {response['open_issues_count']}
🌿 Branch padrão: {response['default_branch']}
📅 Última atualização: {response['updated_at'][:10]}
🔗 URL: {response['html_url']}
        """.strip()

        return {"success": True, "output": summary, "data": response}

    def _file_structure(self, params: dict) -> dict:
        path     = params.get("path", "")
        response = self._get(f"/repos/{self.repo}/contents/{path}")
        if response is None:
            return {"success": False, "output": "Erro ao buscar estrutura de arquivos"}

        summary = f"📁 Estrutura de arquivos ({path or 'raiz'}):\n"
        for item in response:
            icon     = "📁" if item["type"] == "dir" else "📄"
            summary += f"  {icon} {item['name']}\n"

        return {"success": True, "output": summary, "data": response}

    def _deployments(self, params: dict) -> dict:
        response = self._get(f"/repos/{self.repo}/deployments", {"per_page": 10})
        if response is None:
            return {"success": False, "output": "Erro ao buscar deployments"}

        if not response:
            return {"success": True, "output": "Nenhum deployment encontrado."}

        summary = f"🚀 Deployments recentes ({len(response)}):\n"
        for d in response:
            summary += f"  [{d['id']}] env: {d['environment']} - {d['created_at'][:10]}\n"

        return {"success": True, "output": summary, "data": response}

    def _weekly_activity(self, params: dict) -> dict:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            f_commits = executor.submit(self._recent_commits, {"days": 7})
            f_issues  = executor.submit(self._open_issues, {})
            f_prs     = executor.submit(self._pull_requests, {"state": "open"})

            commits = f_commits.result()
            issues  = f_issues.result()
            prs     = f_prs.result()

        summary  = "📊 Resumo semanal:\n\n"
        summary += commits.get("output", "") + "\n"
        summary += issues.get("output",  "") + "\n"
        summary += prs.get("output",     "")

        return {"success": True, "output": summary}

    def _get(self, endpoint: str, params: dict = None):
        try:
            response = requests.get(
                f"{self.base_url}{endpoint}",
                headers=self.headers,
                params=params,
                timeout=GITHUB_TIMEOUT
            )
            if response.status_code == 200:
                return response.json()
            else:
                print(f"GitHub API erro {response.status_code}: {response.text}")
                return None
        except Exception as e:
            print(f"Erro na requisição GitHub: {e}")
            return None
