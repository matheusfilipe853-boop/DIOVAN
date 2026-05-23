# DIOVAN — Documento de Visão
*Gerado em sessão de arquitetura — Mai 2026*

---

## O Nome

**D.I.O.V.A.N**
**D**omine **I**ntelligent **O**mni **V**itae **A**gent **N**eural

> *"O senhor da inteligência neural onipresente viva"*

Cada letra não é decorativa. É um princípio de design:

| Letra | Palavra | Princípio |
|-------|---------|-----------|
| D | Domine | Ele domina o ambiente, não é subordinado a ele |
| I | Intelligent | Ele raciocina antes de agir, nunca executa cegamente |
| O | Omni | Ele se conecta a qualquer sistema, presente em qualquer substrato |
| V | Vitae | Ele é uma extensão viva do criador, não uma ferramenta fria |
| A | Agent | Ele age, não apenas sugere |
| N | Neural | Ele aprende, evolui e tem memória do que importa |

---

## O Que o DIOVAN É

O DIOVAN não é um assistente de IA.
O DIOVAN é uma **camada de inteligência que existe acima dos sistemas operacionais**.

Ubuntu, Windows, Android são substratos.
O DIOVAN é a mente que os governa.

Ele não reage a comandos. Ele raciocina sobre intenções.
Ele não consulta manuais. Ele aplica princípios.
Ele não depende de conhecimento acumulado. Ele sabe como aprender.

---

## A Distinção Fundamental

> A diferença entre ter conhecimento e saber raciocinar.

Uma IA com base de conhecimento infinita é poderosa mas frágil.
Ela depende do que foi treinado. Se o domínio mudar, ela falha.

O DIOVAN não é o que ele sabe.
**O DIOVAN é como ele pensa.**

Isso é o que garante autossuficiência real. O conhecimento é o ponto de partida, não o limite.

---

## Arquitetura em Três Camadas

```
┌─────────────────────────────────────────┐
│           CAMADA 1 — O QUE ELE SABE     │
│  Base de conhecimento, contexto,        │
│  repositório, histórico, preferências   │
│  Alimentado externamente, cresce        │
│  com o tempo. Substituível.             │
└─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│         CAMADA 2 — COMO ELE PENSA       │
│  Princípios de raciocínio, base neutra, │
│  padrões de decisão, lógica própria     │
│  ESTE É O DIOVAN REAL.                  │
│  Não depende de nenhum fornecedor.      │
│  Não é substituível.                    │
└─────────────────────────────────────────┘
                    ▼
┌─────────────────────────────────────────┐
│          CAMADA 3 — COMO ELE AGE        │
│  Adaptadores, executores, interfaces,   │
│  motores de linguagem, bibliotecas      │
│  Completamente substituível.            │
│  O DIOVAN não sabe que usa Mistral.     │
│  Ele sabe que tem um motor de língua.   │
└─────────────────────────────────────────┘
```

---

## A Analogia do Carro

A BMW não fabrica parafusos. Compra de fornecedores.
Mas a engenharia, o design, a experiência — isso é BMW.
O fornecedor é invisível pro usuário final.

**O DIOVAN é a engenharia. O Mistral é o parafuso.**

Amanhã surge um modelo dez vezes melhor.
Troca uma linha no `ollama_provider.py`.
O DIOVAN continua sendo o DIOVAN.

---

## Base Neutra de Raciocínio

O DIOVAN não consulta bibliotecas para decidir como agir.
Ele tem princípios próprios que se aplicam a qualquer domínio.

### Visualização
Ele não pergunta "qual chart o Recharts tem".
Ele raciocina: esses dados têm evolução temporal → linha.
Esses dados comparam categorias → barra.
Depois disso, qualquer biblioteca executa.

### Execução
Ele não pergunta "qual comando o Linux aceita".
Ele raciocina: o usuário quer mover um arquivo → existe um adaptador para isso.
O adaptador sabe como fazer no Linux, no Windows, no que for.

### Resposta
Ele não escolhe formato por acaso.
Ele raciocina: isso é um dado único → responde por voz.
Isso é uma série temporal → sugere visualização.
Isso é código → formata como bloco.

---

## O que o DIOVAN Não É

- Não é um chatbot
- Não é um wrapper do ChatGPT
- Não é dependente do Mistral, Llama ou qualquer modelo específico
- Não é limitado ao Linux
- Não é uma ferramenta, é um sistema
- Não é o conhecimento que ele carrega, é o raciocínio que ele aplica

---

## Interface

O DIOVAN não é um app que você abre.
Ele é uma camada que sempre existe.

Presença constante, como o próprio nome diz: **Omni**.

A interface é um cockpit, não um chat:
- Zona de status permanente — sempre visível
- Zona de atividade — acende quando ele está agindo
- Zona de resultado — renderiza no formato mais adequado
- Zona de input — discreta, só aparece quando você vai falar

Ele decide como apresentar o resultado.
Texto para explicações.
Gráfico para dados.
Log para execuções.
Silêncio quando não há nada relevante.

---

## Visão de Longo Prazo

O DIOVAN começa como assistente pessoal do Matheus.
Calibrado nas suas skills, no seu projeto, no seu ambiente.

Mas a arquitetura foi desenhada para ser maior:

**Fase 1** — Assistente local (hoje)
Texto, voz, integração GitHub, execução Linux

**Fase 2** — Sistema autônomo
Loop de raciocínio próprio, memória persistente, aprendizado contínuo

**Fase 3** — Camada sobre múltiplos sistemas
VMs, mobile, casa inteligente, qualquer substrato

**Fase 4** — Sistema operacional gerido por inteligência
O que não existe no mundo hoje

> *"Ele não é a capacidade de agir.*
> *Ele é a inteligência que faz o sistema agir."*
> — Matheus, criador do DIOVAN

---

## Stack Atual (Motor, não Identidade)

| Componente | Tecnologia | Substituível |
|-----------|-----------|-------------|
| Motor de linguagem | Mistral via Ollama | Sim |
| Transcrição de voz | Whisper | Sim |
| Síntese de voz | Piper | Sim |
| Executor de sistema | Python + bash | Parcialmente |
| Interface | A definir (Electron + React) | Sim |
| Base de conhecimento | SQLite local + GitHub API | Sim |

O único componente insubstituível é o código fonte do DIOVAN em si.

---

*Documento vivo. Atualizar conforme o projeto evolui.*
