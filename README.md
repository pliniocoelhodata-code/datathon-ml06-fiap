# Datathon — esqueleto do repositório

Árvore alinhada ao guia `datathon-README.md`. Implementação do código fica por conta do grupo.

Dependências previstas estão listadas em `pyproject.toml` (pandas, sklearn, torch, MLflow, FastAPI, LangChain, Evidently, Presidio, RAGAS, etc.).

## Observabilidade (Docker)

Na raiz do repositório, com Docker e Docker Compose instalados:

1. Copie as variáveis de ambiente (se ainda não existir): `cp .env.example .env` e ajuste o que for necessário.
2. Suba Prometheus e Grafana: `docker compose up -d`
3. Para encerrar: `docker compose down` (use `docker compose down -v` se quiser remover também os volumes com dados do Prometheus/Grafana).

**Endpoints locais**

| Serviço    | URL                         | Observação                                      |
|------------|-----------------------------|-------------------------------------------------|
| Prometheus | http://localhost:9090       | UI e API de consulta (`/api/v1/query`, etc.).   |
| Grafana    | http://localhost:3000       | Login padrão em `.env.example`: `admin` / `admin` (altere em produção). |

O datasource Prometheus já vem provisionado no Grafana. Configuração de scrape está em `docker/prometheus/prometheus.yml`.
