.PHONY: install train serve test evaluate drift clean help

# Variáveis de ambiente e caminhos
PYTHON = python3
PIP = pip
PYTEST = pytest
UVICORN = uvicorn

help:
	@echo "Comandos disponíveis:"
	@echo "  install   : Instala dependências e o pacote em modo editável"
	@echo "  train     : Executa o treino do modelo baseline com tracking no MLflow"
	@echo "  serve     : Inicia a API FastAPI (Uvicorn)"
	@echo "  test      : Executa testes unitários com coverage (mínimo 60%)"
	@echo "  evaluate  : Executa a avaliação RAGAS contra o Golden Set"
	@echo "  drift     : Executa a análise de drift com Evidently"
	@echo "  clean     : Remove arquivos temporários e caches"

## 1. Instalação (Gap 09: Skills de Engenharia)
install:
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"

## 2. Treinamento e Baseline (Etapa 1)
train:
	@echo "Iniciando treinamento e logando no MLflow..."
	$(PYTHON) src/models/train.py

## 3. Serving e API (Etapa 2)
serve:
	@echo "Iniciando API de predição..."
	$(UVICORN) src.serving.app:app --host 0.0.0.0 --port 8000 --reload

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