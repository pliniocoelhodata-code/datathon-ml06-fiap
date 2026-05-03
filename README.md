# Datathon — Hub de Investimentos com IA (Fase 05)

Este repositório contém a implementação completa do projeto integrador da Fase 05, focado em LLMs, Agentes e MLOps aplicados ao mercado financeiro. O objetivo é atingir o **Nível 2 de maturidade MLOps** com um sistema de predição de preços de ações usando IA.

---

### 🤖 Sistema de Predição e Agente Financeiro
- **Modelo LSTM**: Predição de preços baseada em séries temporais (Open, High, Low, Close, Volume).
- **Agente ReAct**: Assistente inteligente que utiliza ferramentas para responder dúvidas financeiras.
- **RAG (Retrieval-Augmented Generation)**: Base de conhecimento técnica sobre mercado financeiro usando FAISS e embeddings `mxbai-embed-large`.
- **API FastAPI**: Endpoints REST para predições numéricas e interações com o agente.

---

## 🧠 Agente e RAG (Arquitetura)

O projeto implementa um **Agente ReAct** capaz de raciocinar e utilizar ferramentas para fornecer respostas fundamentadas.

### Pipeline RAG
- **Motor**: FAISS (Facebook AI Similarity Search).
- **Embeddings**: `mxbai-embed-large` rodando localmente via Ollama.
- **Estratégia**: Chunking de 500 caracteres com 50 de overlap para manter o contexto semântico.
- **Ferramentas do Agente**:
    1. `search_market_knowledge`: Acessa a base vetorial para conceitos teóricos.
    2. `get_stock_prediction`: Consulta o modelo LSTM para tendências de preço.
    3. `get_technical_indicators`: Calcula indicadores em tempo real (RSI, Médias Móveis).

### Avaliação de Qualidade
Utilizamos o framework **RAGAS** para medir a precisão do sistema em quatro pilares: *Faithfulness*, *Answer Relevancy*, *Context Precision* e *Context Recall*. Complementamos com **LLM-as-judge** para garantir o alinhamento de negócio.

---

## 📊 Observabilidade Completa

- **MLflow**: Tracking de experimentos, métricas de modelo e artefatos
- **Prometheus + Grafana**: Dashboards de métricas operacionais, de negócio e de segurança
- **Drift Detection**: Monitoramento automático de data drift e prediction drift
- **Logs Centralizados**: Loki para agregação e análise de logs

### 🔒 Segurança e Governança
- **Guardrails**: Filtros de entrada/saída e detecção de PII
- **OWASP Top 10**: Mitigação de ameaças específicas para LLMs
- **LGPD Compliance**: Plano de proteção de dados pessoais

### 🧪 Qualidade e Testes
- **Cobertura de Testes**: >60% com pytest
- **RAGAS Evaluation**: Benchmark das 4 métricas obrigatórias contra Golden Set
- **Model Cards**: Documentação completa de modelos e sistema

---

## 🚀 Como Rodar o Projeto (Guia Completo)

### Pré-requisitos
- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gerenciador de ambiente/dependências recomendado)
- Docker & Docker Compose
- Make (opcional, para atalhos)

### 1. Setup Inicial

```bash
# Clone o repositório
git clone <repository-url>
cd datathon-ml06-fiap

# Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações (APIs, portas, etc.)

# Sincronize dependências em ambiente gerenciado pelo uv (recomendado)
uv sync --extra dev

# Execute comandos do projeto com uv (ex.: testes)
uv run make test
```

> Em Ubuntu/WSL (PEP 668), evite `make install` fora de um virtualenv, pois ele usa `pip` global e pode falhar com `externally-managed-environment`.

### Dados e DVC

O dataset principal é versionado com DVC em `data/raw/stock_data.csv.dvc`. O arquivo CSV real usado pelo app fica em `data/raw/stock_data.csv`, mas ele não é versionado diretamente pelo Git.

Remote de leitura do dataset:

```text
https://drive.google.com/drive/folders/1fuibMil4oEUkvbYiB4ULaxPnPmbdF_mw?usp=drive_link
```

Para ambientes novos, baixe ou sincronize essa pasta pelo Google Drive Desktop e configure o caminho local como remote DVC:

```bash
dvc remote add -d localdrive "<CAMINHO_LOCAL_DA_PASTA_SINCRONIZADA>"
dvc pull
```

O projeto não acessa automaticamente o link web do Google Drive durante a execução. O `dvc pull` precisa de um remote local configurado ou do arquivo `data/raw/stock_data.csv` já presente na pasta do projeto.

#### Requisitos para a RAG

Download do Ollama no host ollama.com/download

```bash
# download do modelo
ollama pull mxbai-embed-large

# seviço local
http://localhost:11434
```

### 2. Desenvolvimento Local

#### Treinamento do Modelo
```bash
# Treine o modelo baseline (LSTM) com tracking MLflow
make train
```

#### Testes e Qualidade
```bash
# Execute testes unitários
uv run make test

# Avalie performance do RAG com RAGAS
uv run make evaluate

# Analise drift dos dados
uv run make drift
```

#### API Local (Desenvolvimento)
```bash
# Inicie API com reload automático
uv run make api-dev
# Acesse: http://localhost:8000/docs
```

### 3. Ambiente Completo com Docker

```bash
# Suba toda a stack (API + MLflow + Observabilidade)
docker compose up -d --build

# Ou apenas a API isoladamente
make docker-api-build
make docker-api-run
```

### 4. Acesse os Serviços

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **API FastAPI** | http://localhost:8000/docs | Documentação Swagger da API de predições |
| **MLflow UI** | http://localhost:5000 | Tracking de experimentos e modelos |
| **Grafana** | http://localhost:3000 | Dashboards: Business Metrics, Infrastructure e Security & Governance (user: admin, pass: admin123) |
| **Prometheus** | http://localhost:9090 | Consulta de métricas operacionais |

---

## 📋 Workflow de Uso

### Para Desenvolvedores
1. **Setup**: `uv sync --extra dev`
2. **Desenvolvimento**: Modifique código em `src/`
3. **Teste**: `uv run make test`
4. **Iteração**: `uv run make api-dev` para testar API

### Para Data Scientists
1. **Treino**: `uv run make train` (modelo salvo em MLflow)
2. **Avaliação**: `uv run make evaluate` (métricas RAGAS)
3. **Monitoramento**: `uv run make drift` (análise de drift)

### Para Operações
1. **Deploy**: `docker compose up -d`
2. **Monitoramento**: Acesse Grafana para dashboards
3. **Logs**: Verifique Loki via Grafana

---

## 🏗️ Arquitetura Técnica

### Pipeline MLOps
```
Dados Brutos → Feature Engineering → Treino (MLflow) → API → Monitoramento
     ↓              ↓                      ↓          ↓          ↓
    DVC          Pandas/Numpy           LSTM     FastAPI   Prometheus
                                                          Grafana
```

### Componentes Principais
- **src/models/**: Treinamento e baseline
- **src/serving/**: API FastAPI e endpoints
- **src/agent/**: Agente ReAct com ferramentas
- **src/monitoring/**: Drift detection e métricas
- **evaluation/**: RAGAS e benchmarks
- **tests/**: Suíte de testes

---

## 📈 Métricas e Monitoramento

### Métricas de Modelo (MLflow)
- RMSE, MAE, R²
- Parâmetros de treinamento
- Artefatos (modelos, scalers)

### Métricas Operacionais (Prometheus)
- Latência de predições
- Taxa de erro por endpoint
- Uso de recursos
- Eventos de guardrails, bloqueios e redações de PII no fluxo do agente

### Drift Detection
- Population Stability Index (PSI)
- Share of drifted columns
- Alertas automáticos no Grafana

---

## 🔐 Segurança

- **Input Validation**: Guardrails em prompts e dados
- **PII Detection**: Identificação automática de dados sensíveis
- **Rate Limiting**: Controle de uso da API
- **OWASP Compliance**: Mitigação de 5+ ameaças LLM
- **Security Dashboard**: Painel Grafana `Datathon ML - Security & Governance`

---

## 📚 Documentação Adicional

- [System Model](docs/SYSTEM_MODEL.md): Detalhes do modelo LSTM
- [System Card](docs/SYSTEM_CARD.md): Arquitetura completa
- [LGPD Plan](docs/LGPD_PLAN.md): Conformidade de dados
- [OWASP Mapping](docs/OWASP_MAPPING.md): Segurança LLM
- [Metric Mapping](docs/METRIC_MAPPING.md): Métricas de negócio
- [Monitoring Guide](docs/MONITORING_README.md): Guia completo de observabilidade
- [Benchmark LLM](docs/BENCHMARK.md): Comparativo de performance e quantização
- [Evaluation Report](docs/EVALUATION_REPORT.md): Relatório de métricas RAGAS e LLM-as-judge

---

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

Para desenvolvimento local, use `uv run make test` antes de commitar.
