# Datathon — Hub de Investimentos com IA (Fase 05)

Este repositório contém a implementação do projeto integrador da Fase 05, focado em LLMs, Agentes e MLOps aplicados ao mercado financeiro. O objetivo é atingir o **Nível 2 de maturidade MLOps**.

---

## 🚀 Como Começar (Workflow)

Este projeto utiliza um `Makefile` para padronizar as tarefas de desenvolvimento e garantir a reprodutibilidade do pipeline, evitando Gaps de engenharia de software.

1.  **Instalação**: Configure seu ambiente virtual e dependências:
    ```bash
    make install
    ```
2.  **Qualidade**: Garante que o código respeita os critérios de teste (mínimo 60% de cobertura):
    ```bash
    make test
    ```
3.  **Avaliação RAG**: Valida a performance do Agente contra o *Golden Set* de 20 casos usando **RAGAS**:
    ```bash
    make evaluate
    ```
4.  **Monitoramento de Drift**: Gera o relatório de saúde dos dados e predições com **Evidently**:
    ```bash
    make drift
    ```

---

## 📊 Observabilidade (Docker)

A infraestrutura de monitoramento é essencial para evitar o Gap de ausência de monitoramento de modelos. Utilizamos Prometheus e Grafana para telemetria e dashboards.

Na raiz do repositório, com Docker e Docker Compose instalados:

1. **Configuração**: Copie as variáveis de ambiente: `cp .env.example .env` e ajuste as chaves necessárias.
2. **Setup**: Suba os serviços de monitoramento:
    ```bash
    docker compose up -d
    ```
3. **Encerramento**: Para parar os serviços: `docker compose down` (use `-v` para remover volumes de dados).

### Endpoints Locais

| Serviço     | URL                         | Observação                                      |
|-------------|-----------------------------|-------------------------------------------------|
| Prometheus  | http://localhost:9090       | UI e API de consulta para métricas operacionais. |
| Grafana     | http://localhost:3000       | Dashboards de métricas de negócio e drift. |
| API FastAPI | http://localhost:8000/docs  | Documentação Swagger do Agente e modelo.         |

---

## 🛠️ Pilares do Projeto

### 1. Dados e Baseline (Etapa 1)
* **DVC**: Versionamento de dados brutos e processados para garantir reprodutibilidade.
* **MLflow**: Tracking padronizado de métricas (AUC, F1, Precisão), parâmetros e artefatos.

### 2. LLM e Agente (Etapa 2)
* **Agente ReAct**: Implementação com ≥ 3 ferramentas customizadas para o domínio financeiro.
* **RAG Pipeline**: Recuperação de contexto baseada nos dados fornecidos pela empresa.

### 3. Avaliação e Monitoramento (Etapa 3)
* **Golden Set**: Conjunto de ≥ 20 pares (query/expected) para validação técnica.
* **RAGAS**: Cálculo das 4 métricas obrigatórias: Faithfulness, Answer Relevancy, Context Precision e Context Recall.
* **Drift Detection**: Monitoramento proativo de data e prediction drift via Evidently.

### 4. Segurança e Governança (Etapa 4)
* **Guardrails**: Implementação de filtros de input/output e detecção de PII.
* **OWASP Top 10**: Mapeamento e mitigação de pelo menos 5 ameaças para LLMs.
* **Model/System Cards**: Documentação completa sobre o funcionamento, riscos e limitações do sistema.

---

## 📂 Estrutura do Repositório

```text
├── data/              # Dados e Golden Set (20 pares)
├── src/               # Código fonte (Features, Models, Agent, Serving)
├── evaluation/        # Scripts de RAGAS e Benchmarks
├── monitoring/        # Scripts de Drift e métricas Prometheus
├── docs/              # Model Card, System Card e Plano LGPD
├── tests/             # Suíte de testes (pytest)
└── Makefile           # Atalhos de automação do projeto