.PHONY: install train serve api api-dev docker-api-build docker-api-run test evaluate drift clean help

# Variáveis de ambiente e caminhos
PYTHON = python3
PIP = pip
PYTEST = pytest
UVICORN = uvicorn
API_HOST ?= 0.0.0.0
API_PORT ?= 8000
DOCKER_API_IMAGE ?= datathon-predict-api

help:
	@echo "Comandos disponíveis:"
	@echo "  install          : Instala dependências e o pacote em modo editável"
	@echo "  train            : Executa o treino do modelo baseline com tracking no MLflow"
	@echo "  serve / api-dev  : Inicia a API FastAPI com reload (desenvolvimento)"
	@echo "  api              : Inicia a API FastAPI sem reload (produção local)"
	@echo "  docker-api-build : Constrói a imagem Docker da API (Dockerfile em src/serving/)"
	@echo "  docker-api-run   : Sobe o container da API (usa API_PORT; opcional: .env)"
	@echo "  test             : Executa testes unitários com coverage (mínimo 60%)"
	@echo "  evaluate         : Executa a avaliação RAGAS contra o Golden Set"
	@echo "  drift            : Executa a análise de drift com Evidently"
	@echo "  clean            : Remove arquivos temporários e caches"

## 1. Instalação (Gap 09: Skills de Engenharia)
install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

## 2. Treinamento e Baseline (Etapa 1)
train:
	@echo "Iniciando treinamento e logando no MLflow..."
	$(PYTHON) src/models/train.py

## 3. Serving e API (Etapa 2)
# PYTHONPATH=. garante imports src.* a partir da raiz do repositório
serve: api-dev

api-dev:
	@echo "Iniciando API de predição (reload) em http://$(API_HOST):$(API_PORT) ..."
	PYTHONPATH=. $(UVICORN) src.serving.app:app --host $(API_HOST) --port $(API_PORT) --reload

api:
	@echo "Iniciando API de predição em http://$(API_HOST):$(API_PORT) ..."
	PYTHONPATH=. $(UVICORN) src.serving.app:app --host $(API_HOST) --port $(API_PORT)

docker-api-build:
	@echo "Construindo imagem $(DOCKER_API_IMAGE) ..."
	docker build -f src/serving/Dockerfile -t $(DOCKER_API_IMAGE) .

docker-api-run:
	@echo "Subindo container $(DOCKER_API_IMAGE) na porta $(API_PORT) ..."
	@if [ -f .env ]; then \
		docker run --rm -p $(API_PORT):8000 --env-file .env $(DOCKER_API_IMAGE); \
	else \
		docker run --rm -p $(API_PORT):8000 $(DOCKER_API_IMAGE); \
	fi

## 4. Qualidade e Testes (Gap 04: Cobertura de Testes)
test:
	@echo "Executando testes com pytest..."
	$(PYTEST) tests/ --cov=src --cov-report=term-missing --cov-fail-under=60

## 5. Avaliação RAGAS (Etapa 3: Qualidade LLM)
evaluate:
	@echo "Executando benchmark RAGAS..."
	$(PYTHON) evaluation/ragas_eval.py

## 6. Monitoramento de Drift (Etapa 3: Observabilidade)
drift:
	@echo "Executando análise de Data Drift..."
	$(PYTHON) src/monitoring/drift.py

## Limpeza de ambiente
clean:
	rm -rf .pytest_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	@echo "Limpeza concluída."