import logging
import json
import asyncio
from src.agent.react_agent import get_financial_agent
from evaluation.ragas_eval import evaluate_rag_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_agent_evaluation():
    """
    Performs the Financial Agent evaluation against the Golden Set using Ragas asynchronously.
    """
    # starts the agent
    agent = get_financial_agent()

    def rag_fn(query):
        """
        Synchronous wrapper function for the agent.
        The evaluate_rag_pipeline will handle parallel execution in threads.
        """
        response = agent.invoke({"input": query})
        return response["output"], response.get("contexts", [])

    logger.info("Starting Ragas evaluation...")
    
    try:
        metrics = await evaluate_rag_pipeline(
            golden_set_path="data/golden_set/sample.json",
            rag_fn=rag_fn,
            max_concurrency=1, # limita quantas chamadas ao LLM rodam em paralelo. ex: 2 ou 3 dependendo da gpu/cpu
            sample_size=3    # limitar a quantidade de submits do golden set
        )
        
        # results
        for metric, score in metrics.items():
            print(f"{metric.capitalize()}: {score:.4f}")
        print("="*30)
        
        with open("evaluation/latest_results.json", "w", encoding='utf-8') as f:
            json.dump(metrics, f, indent=4, ensure_ascii=False)
            
    except Exception as e:
        logger.error(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_agent_evaluation())
