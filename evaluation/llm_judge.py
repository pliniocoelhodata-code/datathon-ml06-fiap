import json
import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate

class LLMAsJudge:
    def __init__(self, model_name="llama3.2"):
        self.llm = ChatOllama(model=model_name, temperature=0)
        self.prompt = PromptTemplate.from_template("""
        Você é um auditor financeiro sênior. Sua tarefa é avaliar a resposta de um assistente de IA com base em três critérios.

        Pergunta do Usuário: {query}
        Resposta da IA: {answer}
        Resposta Esperada (Ground Truth): {expected}

        Avalie de 1 a 5 para cada critério abaixo:

        1. ACURÁCIA TÉCNICA: A resposta contém conceitos financeiros corretos e está alinhada com o que era esperado?
        2. ALINHAMENTO DE NEGÓCIO: A resposta é útil para um investidor e mantém um tom profissional e cauteloso?
        3. FIDELIDADE (ANTI-ALUCINAÇÃO): A resposta se mantém fiel aos fatos ou inventa dados não solicitados?

        Responda APENAS em formato JSON como no exemplo:
        {{"acuracia": 5, "negocio": 4, "fidelidade": 5, "comentario": "Explicação breve"}}
        """)

    def judge_answer(self, query, answer, expected):
        chain = self.prompt | self.llm
        response = chain.invoke({
            "query": query,
            "answer": answer,
            "expected": expected
        })
        try:
            return json.loads(response.content)
        except:
            # Fallback caso a LLM não responda em JSON puro
            return {"error": "Falha ao processar avaliação"}

def run_llm_judge(golden_set_path, agent_fn):
    with open(golden_set_path, encoding='utf-8') as f:
        samples = json.load(f)
    
    judge = LLMAsJudge()
    results = []
    
    print(f"Iniciando LLM-as-judge para {len(samples)} amostras...")
    
    for item in samples[:5]: # Rodando em 5 para teste rápido
        print(f"Avaliando query: {item['query'][:50]}...")
        agent_res = agent_fn(item['query'])
        evaluation = judge.judge_answer(item['query'], agent_res['output'], item['expected_answer'])
        results.append({
            "query": item['query'],
            "scores": evaluation
        })
    
    return results

if __name__ == "__main__":
    from src.agent.react_agent import get_financial_agent
    agent = get_financial_agent()
    
    def agent_fn(q):
        return agent.invoke({"input": q})
        
    evaluation_results = run_llm_judge("data/golden_set/sample.json", agent_fn)
    print(json.dumps(evaluation_results, indent=2, ensure_ascii=False))
