from langchain.tools import tool
from src.agent.rag_pipeline import RAGPipeline
import os

rag_internal = RAGPipeline()

@tool
def search_market_knowledge(query: str) -> str:
    """
    Consulta a base de conhecimento interna sobre mercado financeiro.
    Útil para: Análise Técnica, Fundamentalista, Macroeconomia, Commodities e Eventos Corporativos.
    Sempre use esta ferramenta quando a pergunta envolver conceitos técnicos ou dados históricos específicos.
    """
    return rag_internal.get_context(query)

@tool
def get_stock_prediction(symbol: str) -> str:
    """
    Acessa o modelo de ML (LSTM) para prever a tendência de fechamento de uma ação.
    Input deve ser o ticker da ação (ex: PETR4, VALE3).
    """
    # this is where the logic for loading the model from src/models/ and making the prediction comes in.
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
