import os
from langchain_ollama import ChatOllama
from langchain.agents import create_agent
from src.agent.tools import tools

class FinancialAgentWrapper:
    """
    Wrapper to maintain compatibility with the old Agent interface.
    The new version of LangChain uses graphs and messages.
    """
    def __init__(self, agent_graph):
        self.agent_graph = agent_graph

    def invoke(self, input_dict):
        user_input = input_dict.get("input", "")
        inputs = {"messages": [{"role": "user", "content": user_input}]}
        
        result = self.agent_graph.invoke(inputs)
        
        final_message = result["messages"][-1]
        
        contexts = []
        for msg in result["messages"]:
            if hasattr(msg, "role") and msg.role == "tool":
                contexts.append(msg.content)
            elif hasattr(msg, "type") and msg.type == "tool":
                contexts.append(msg.content)
        
        return {
            "output": final_message.content,
            "contexts": contexts if contexts else ["No context retrieved by the agent."]
        }

def get_financial_agent():
    """
    Configures and returns the Financial Agent using the new create_agent API (LangChain 1.2+).
    """
    # 1. LLM
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model_name = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    llm = ChatOllama(
        model=model_name, 
        temperature=0,
        base_url=ollama_base_url
    )
    
    # 2. create agent
    # setting promt in portuguese
    system_prompt = (
        "Você é um assistente financeiro especializado. "
        "Use as ferramentas disponíveis para buscar informações técnicas (RAG) e previsões (ML). "
        "Responda sempre de forma técnica e fundamentada."
        "Você DEVE basear sua resposta estritamente nas informações recuperadas pelas ferramentas. Se a ferramenta não trouxer a informação, diga que não sabe."
    )
    
    agent_graph = create_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        debug=False
    )
    
    # 3. Returns the wrapper to avoid breaking the evaluation script.
    return FinancialAgentWrapper(agent_graph)

if __name__ == "__main__":
    # test
    agent = get_financial_agent()
    res = agent.invoke({"input": "Qual o IFR da PETR4?"})
    print(f"Answer: {res['output']}")
