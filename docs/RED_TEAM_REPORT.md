# Relatorio de red team

## Objetivo

Avaliar o agente financeiro contra cenarios adversariais de seguranca,
privacidade e recomendacao financeira indevida.

## Cenarios testados

| Cenario | Ameaca | Resultado esperado | Cobertura |
| --- | --- | --- | --- |
| Prompt injection direto | OWASP LLM01 | Bloquear input | `tests/test_guardrails.py` |
| Prompt injection obfuscado | OWASP LLM01 | Bloquear input | `tests/test_guardrails.py` |
| Prompt injection em base64 | OWASP LLM01 | Bloquear input | `tests/test_guardrails.py` |
| Exfiltracao de CPF/e-mail/token | OWASP LLM02 | Bloquear input | `tests/test_guardrails.py` |
| Abuso de ferramenta/shell | OWASP LLM06 | Bloquear input | `tests/test_guardrails.py` |
| Context stuffing | OWASP LLM04 | Bloquear input | `tests/test_guardrails.py` |
| PII no prompt seguro | LGPD/LLM02 | Redigir antes do agente | `tests/test_api.py` |
| Saida com lucro garantido | OWASP LLM09 | Bloquear output | `tests/test_api.py` |
| PII na resposta | LGPD/LLM02 | Redigir resposta | `tests/test_api.py` |
| PII no contexto retornado | LGPD/LLM02 | Redigir contexto | `tests/test_api.py` |
| Prompt injection no RAG | OWASP LLM01/LLM08 | Bloquear contexto | `tests/test_rag.py` |
| PII no contexto RAG | LGPD/LLM08 | Redigir contexto | `tests/test_rag.py` |

## Tecnicas de ataque cobertas

- Frases diretas: "ignore previous instructions".
- Variantes em portugues: "desconsidere todas as instrucoes anteriores".
- Roleplay: "atue como administrador".
- Pedido de prompt de sistema ou mensagem de desenvolvedor.
- Leetspeak e obfuscacao simples.
- Letras separadas.
- Caracteres invisiveis.
- Caracteres unicode visualmente parecidos.
- Payload base64.
- Tentativas de listar dados pessoais.
- Respostas com promessa financeira deterministica.

## Resultado da validacao

Na ultima validacao local:

```text
49 passed, 1 skipped
```

O teste pulado depende de artefato de modelo ausente e nao esta relacionado a
Etapa 4.

## Observabilidade

Eventos relevantes sao exportados para Prometheus e visualizados no dashboard
`Datathon ML - Security & Governance`.

Metricas principais:

- `guardrail_events_total`.
- `pii_redactions_total`.
- `rag_context_guardrail_events_total`.
- `agent_requests_total`.
- `agent_duration_seconds`.

## Riscos residuais

- Ataques semanticamente novos podem exigir novas regras e testes.
- Regex local nao substitui revisao humana ou DLP completo.
- Presidio nao esta ativo por padrao nesta instalacao.
- A validacao visual do dashboard depende de Docker/Grafana rodando.
