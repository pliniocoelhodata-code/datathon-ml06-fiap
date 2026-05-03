# Plano de conformidade LGPD

## Escopo

Este plano cobre o endpoint do agente financeiro (`/agent`), o pipeline RAG, logs,
metricas de seguranca e tratamento de dados pessoais em prompts, respostas e
contextos recuperados.

O sistema nao deve solicitar nem depender de dados pessoais para responder
perguntas financeiras. Quando PII aparece por erro do usuario, por resposta do
modelo ou por contexto recuperado, ela deve ser redigida antes de persistencia,
retorno ou observabilidade.

## Dados pessoais considerados

O detector atual cobre, por padrao:

- CPF brasileiro.
- E-mail.
- Telefone.
- Chaves com padrao de API key.

O detector usa regex local por padrao. Presidio permanece opcional no codigo, mas
nao e requisito de instalacao porque suas dependencias atuais conflitam com
`dvc-gdrive`/`pydrive2`.

## Controles implementados

- `InputGuardrail` valida o prompt antes de chamar o agente.
- PII em input e redigida antes de `agent.invoke(...)`.
- `OutputGuardrail` valida a resposta antes de retornar ao usuario.
- PII em resposta e contextos retornados e redigida.
- Contextos RAG passam por guardrail antes de chegar ao LLM.
- Prompt injection, exfiltracao de dados, abuso de ferramentas e context stuffing
  sao bloqueados.
- Saidas com recomendacao financeira indevida, como "lucro garantido", sao
  bloqueadas.
- Sentry esta configurado com `send_default_pii=False`.
- Logs de bloqueio do agente registram `user_id`, tipo de deteccao e tipo de erro,
  sem prompt bruto, output bruto ou contexto bruto.

## Observabilidade

As metricas de seguranca estao expostas em Prometheus:

- `agent_requests_total{status}`.
- `agent_duration_seconds`.
- `guardrail_events_total{stage, action, detection}`.
- `pii_redactions_total{surface}`.
- `rag_context_guardrail_events_total{action, detection}`.

O dashboard `Datathon ML - Security & Governance` consolida bloqueios,
redacoes de PII, eventos em contexto RAG e latencia do agente.

## Retencao e minimizacao

- Prompts brutos nao sao registrados nos logs de seguranca.
- Respostas bloqueadas nao sao retornadas ao usuario.
- Contextos com PII sao redigidos antes de aparecerem na resposta da API.
- Segredos e credenciais nao devem ser versionados. Configuracoes locais de DVC
  devem usar `.dvc/config.local` quando contiverem caminhos ou credenciais locais.

## Riscos residuais

- Regex pode nao cobrir todos os formatos de PII existentes.
- Presidio nao esta habilitado por padrao nesta instalacao.
- Logs de outras partes do sistema, como predicao numerica, ainda podem conter
  campos operacionais como `username`; recomenda-se revisar essa camada antes de
  producao.
- O modelo pode gerar conteudo indevido ainda nao coberto pelos padroes atuais.
- Dependencias externas de observabilidade podem emitir warnings ou metadados nao
  controlados pelo projeto.

## Recomendacoes

- Ampliar o detector de PII com CNPJ, endereco e dados bancarios se o escopo
  evoluir.
- Criar politica de retencao para logs e metricas.
- Revisar periodicamente os prompts adversariais em `tests/test_guardrails.py`.
- Validar visualmente o dashboard de seguranca no Grafana quando Docker estiver
  disponivel.
