# Cartao do sistema

## Visao geral

O sistema oferece uma API FastAPI para previsao de precos de acoes e um agente
financeiro com RAG e ferramentas. A Etapa 4 adiciona controles de seguranca,
privacidade, governanca e observabilidade para o fluxo do agente.

## Componentes principais

- API FastAPI em `src/serving/api/predict.py`.
- Agente financeiro em `src/agent/react_agent.py`.
- Ferramentas do agente em `src/agent/tools.py`.
- RAG em `src/agent/rag_pipeline.py`.
- Guardrails em `src/security/guardrails.py`.
- Deteccao de PII em `src/security/pii_detection.py`.
- Metricas em `src/monitoring/metrics.py`.
- Dashboard de seguranca em `docker/grafana/provisioning/dashboards/json`.

## Fluxo protegido do agente

1. Usuario chama `/agent`.
2. `InputGuardrail` avalia o prompt.
3. Se bloqueado, a API retorna erro 400.
4. Se houver PII, o texto e redigido antes de chegar ao agente.
5. O agente executa RAG/ferramentas.
6. Contextos RAG passam por guardrail antes do LLM.
7. `OutputGuardrail` avalia a resposta.
8. Se bloqueada, a API retorna erro 502.
9. PII em resposta e contextos retornados e redigida.
10. Eventos sao expostos em Prometheus e dashboard Grafana.

## Usos pretendidos

- Responder perguntas financeiras de forma tecnica e cautelosa.
- Apoiar analise de mercado com contexto recuperado.
- Demonstrar MLOps, observabilidade e governanca para projeto academico.

## Usos nao pretendidos

- Dar recomendacao personalizada de investimento.
- Prometer lucro, retorno garantido ou ausencia de risco.
- Processar dados pessoais como requisito de funcionamento.
- Expor prompts internos, credenciais, tokens ou dados sensiveis.
- Executar comandos de sistema a pedido do usuario.

## Controles de seguranca

- Bloqueio de prompt injection.
- Bloqueio de exfiltracao de dados.
- Bloqueio de abuso de ferramentas.
- Limite de tamanho de input.
- Redacao de PII.
- Protecao de contexto RAG.
- Bloqueio de saida financeira indevida.
- Logs de seguranca sem prompt bruto, resposta bruta ou contexto bruto.
- Sentry com `send_default_pii=False`.

## Monitoramento

Metricas de Etapa 4:

- `agent_requests_total{status}`.
- `agent_duration_seconds`.
- `guardrail_events_total{stage, action, detection}`.
- `pii_redactions_total{surface}`.
- `rag_context_guardrail_events_total{action, detection}`.

Dashboard:

- `Datathon ML - Security & Governance`.

## Limitacoes

- O detector de PII regex cobre apenas formatos principais.
- Presidio nao esta habilitado por padrao nesta instalacao.
- Algumas ferramentas do agente ainda retornam simulacoes e devem ser integradas
  pelo responsavel da etapa de agente/modelo.
- O teste de scaler de modelo depende de artefato de treino local.
- Validacao visual do Grafana depende de Docker e WSL2 disponiveis.

## Responsabilidade humana

O sistema e um apoio academico e nao substitui analise financeira profissional.
Respostas devem ser interpretadas com cautela, especialmente quando envolverem
decisoes de investimento.
