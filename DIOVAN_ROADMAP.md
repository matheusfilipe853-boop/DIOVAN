# DIOVAN — Plano de Ação de Hoje

## Contexto
DIOVAN está funcional em modo texto com integração GitHub.
O objetivo hoje é solidificar a identidade, corrigir alucinações e preparar a base para evolução.

---

## SESSÃO DE HOJE — 4 blocos em ordem

### BLOCO 1 — Registrar o DIOVAN no Ollama
**Objetivo:** trocar de modelo genérico para identidade própria

```bash
# Coloca os arquivos na raiz do projeto diovan/
cp Modelfile.combined ~/Documentos/diovan/Modelfile.combined
cd ~/Documentos/diovan

# Baixa o Mistral se ainda não tiver
ollama pull mistral

# Cria o modelo DIOVAN
ollama create diovan -f Modelfile.combined

# Confirma que foi criado
ollama list
```

Depois abre `core/llm/providers/ollama_provider.py` e muda:
```python
def __init__(self, model="diovan", ...):
```

**Resultado esperado:** `make start` e o agente já responde como DIOVAN

---

### BLOCO 2 — Corrigir alucinações no Orquestrador
**Objetivo:** DIOVAN busca contexto real antes de responder, nunca inventa

Atualizar `core/orchestrator.py` com lógica ReAct:
- Sempre tenta `search_file` quando há termos técnicos na pergunta
- Se o contexto retornado for vazio, não responde — pergunta mais
- Prioriza arquivos de código sobre documentação nos resultados

Testar com:
```
Como está implementado o OAuth Google no projeto?
```
Resultado esperado: ele lê o `route.ts` real e explica com base no código

---

### BLOCO 3 — Cache de contexto GitHub
**Objetivo:** reduzir latência nas requisições repetidas

Criar `core/cache.py` simples com TTL de 5 minutos:
- Salva resultado das buscas GitHub em memória
- Na próxima pergunta similar, usa o cache em vez de buscar de novo
- Invalida automaticamente após o TTL

Isso reduz o tempo de resposta em perguntas seguidas sobre o mesmo tema

---

### BLOCO 4 — Testar e documentar o que funciona
**Objetivo:** fechar o dia com clareza do que está sólido

Fazer 5 perguntas reais ao DIOVAN e anotar:
- O que respondeu corretamente com contexto real
- O que ainda alucionou
- O que ficou lento

Criar `knowledge/diovan-status.md` com esse registro.
Esse arquivo vai virar base de conhecimento do próprio DIOVAN sobre si mesmo.

---

## ORDEM DE PRIORIDADE
1. Bloco 1 — sem isso os outros blocos não fazem sentido
2. Bloco 2 — é o problema mais crítico hoje
3. Bloco 3 — melhoria de performance
4. Bloco 4 — fecha o dia com clareza

---

## PRÓXIMAS SESSÕES (não hoje)
- Implementar padrão ReAct completo com loop de tentativas
- Adicionar memória persistente local com SQLite
- Integrar Whisper para entrada por voz
- Criar interface gráfica mínima
- Configurar Piper para saída por voz
