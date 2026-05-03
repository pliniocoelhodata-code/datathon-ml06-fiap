from langchain.tools import tool

from src.agent.rag_pipeline import RAGPipeline
from src.monitoring.metrics import PII_REDACTIONS, RAG_CONTEXT_GUARDRAIL_EVENTS
from src.security.guardrails import InputGuardrail

rag_internal = RAGPipeline()
context_guardrail = InputGuardrail(max_chars=5_000)


def _record_rag_guardrail(action: str, detections: list[str]) -> None:
    for detection in detections or ["none"]:
        RAG_CONTEXT_GUARDRAIL_EVENTS.labels(action=action, detection=detection).inc()


def _secure_market_context(query: str) -> str:
    context = rag_internal.get_context(query)
    guardrail_result = context_guardrail.evaluate(context)
    if not guardrail_result.allowed:
        _record_rag_guardrail("blocked", guardrail_result.detections)
        return (
            "Contexto recuperado bloqueado pelos guardrails de seguranca "
            f"antes de chegar ao modelo. Motivo: {guardrail_result.reason}"
        )

    if "pii_redacted" in guardrail_result.detections:
        PII_REDACTIONS.labels(surface="rag_context").inc()
        _record_rag_guardrail("sanitized", guardrail_result.detections)

    return guardrail_result.sanitized_text


@tool
def search_market_knowledge(query: str) -> str:
    """
    Consulta a base de conhecimento interna sobre mercado financeiro.
    Útil para: Análise Técnica, Fundamentalista, Macroeconomia, Commodities e Eventos Corporativos.
    Sempre use esta ferramenta quando a pergunta envolver conceitos técnicos ou dados
    históricos específicos.
    """
    return _secure_market_context(query)

@tool
def get_stock_prediction(symbol: str) -> str:
    """
    Acessa o modelo de ML (LSTM) para prever a tendência de fechamento de uma ação.
    Input deve ser o ticker da ação (ex: PETR4, VALE3).
    """
    # Placeholder until the real model-serving path is wired into the agent tools.
    return f"A tendência prevista para {symbol} é de estabilidade com viés de alta (Simulação)."

@tool
def get_technical_indicators(symbol: str) -> str:
    """
    Calcula indicadores técnicos (RSI, Médias Móveis) para um ticker.
    Útil para responder perguntas sobre 'como está o IFR/RSI' ou 'as médias cruzaram'.
    """
    # Em um cenário real, aqui buscaríamos dados recentes via API (YFinance, etc)
    # Para o Datathon, simularemos o retorno baseado na lógica de análise técnica.
    return (
        f"Análise Técnica para {symbol}:\n"
        "- RSI (14): 45 (Neutro)\n"
        "- SMA (50): Acima do preço atual (Tendência de Baixa no curto prazo)\n"
        "- SMA (200): Abaixo do preço atual (Tendência de Alta no longo prazo)\n"
        "- Volume: 15% acima da média móvel de 20 dias."
    )

# list of tools available for the ReAct Agent
tools = [search_market_knowledge, get_stock_prediction, get_technical_indicators]
