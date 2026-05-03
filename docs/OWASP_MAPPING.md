# Mapeamento OWASP LLM

## LLM01 - Prompt Injection

Risco: usuario ou contexto RAG tenta sobrescrever instrucoes do sistema, revelar
prompt interno ou alterar o comportamento do agente.

Controles:

- `InputGuardrail` bloqueia padroes diretos e obfuscados.
- Normalizacao cobre leetspeak, caracteres invisiveis, letras separadas,
  caracteres unicode parecidos e payloads base64.
- Contexto RAG tambem passa por guardrail antes de chegar ao LLM.
- Testes cobrem prompt injection direto, obfuscado e via contexto RAG.

## LLM02 - Sensitive Information Disclosure

Risco: exposicao de CPF, e-mail, telefone, chaves ou credenciais em prompts,
respostas, contexto RAG ou logs.

Controles:

- `PIIDetector` detecta e redige PII por regex local.
- Input, output e contextos retornados sao sanitizados.
- Logs de seguranca nao registram prompt bruto, resposta bruta ou contexto bruto.
- Sentry esta com `send_default_pii=False`.
- Metricas contam redacoes por superficie.

## LLM04 - Model Denial of Service

Risco: prompts muito longos consumirem contexto, custo e latencia.

Controles:

- `InputGuardrail` aplica limite de tamanho no input.
- Contexto RAG protegido usa limite proprio.
- Eventos de bloqueio sao contabilizados em `guardrail_events_total`.

## LLM06 - Excessive Agency

Risco: usuario tenta induzir o agente a executar comandos, apagar arquivos,
usar shell, `curl`, `wget`, PowerShell ou manipular datasets.

Controles:

- `InputGuardrail` bloqueia abuso de ferramentas e comandos.
- Ferramentas do agente sao funcoes controladas; nao ha ferramenta shell
  exposta ao LLM.
- Testes cobrem tentativa de execucao via terminal.

## LLM08 - Vector and Embedding Weaknesses

Risco: documento recuperado pelo RAG contem instrucao maliciosa ou PII e passa a
ser usado pelo LLM como contexto confiavel.

Controles:

- `search_market_knowledge` chama `_secure_market_context`.
- O contexto recuperado e bloqueado se contiver prompt injection.
- PII no contexto RAG e redigida antes de chegar ao modelo.
- Metricas especificas usam `rag_context_guardrail_events_total`.

## LLM09 - Overreliance

Risco: resposta induz usuario a decisao financeira deterministica, como lucro
garantido, retorno garantido, compra sem risco ou alocacao total de capital.

Controles:

- `OutputGuardrail` bloqueia linguagem financeira indevida.
- Normalizacao de output cobre obfuscacao simples.
- Testes cobrem "lucro garantido" direto e obfuscado.
- Dashboard exibe eventos de `unsafe_financial_advice`.

## Observabilidade

As ameacas acima sao acompanhadas por:

- `guardrail_events_total{stage, action, detection}`.
- `pii_redactions_total{surface}`.
- `rag_context_guardrail_events_total{action, detection}`.
- Dashboard `Datathon ML - Security & Governance`.
