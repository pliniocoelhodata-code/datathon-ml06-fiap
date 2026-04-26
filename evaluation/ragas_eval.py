import json
import logging
import asyncio
import numpy as np
from typing import Callable, Any

from datasets import Dataset
from ragas import evaluate, RunConfig
from ragas.metrics import (
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from langchain_ollama import ChatOllama, OllamaEmbeddings

logger = logging.getLogger(__name__)

async def evaluate_rag_pipeline(
    golden_set_path: str,
    rag_fn: Callable[[str], Any],
    max_concurrency: int = 1,
    sample_size: int = None
) -> dict[str, float]:
    """
    Evaluates the RAG pipeline against a golden set asynchronously.
    """
    with open(golden_set_path, encoding='utf-8') as f:
        golden_set = json.load(f)

    if sample_size:
        golden_set = golden_set[:sample_size]

    semaphore = asyncio.Semaphore(max_concurrency)

    async def wrapped_rag_fn(item):
        async with semaphore:
            logger.info(f"Processando query: {item['query'][:50]}...")
            try:
                if asyncio.iscoroutinefunction(rag_fn):
                    answer, contexts = await rag_fn(item["query"])
                else:
                    answer, contexts = await asyncio.to_thread(rag_fn, item["query"])
                
                return {
                    "question": item["query"],
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": item["expected_answer"],
                }
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                return {
                    "question": item["query"],
                    "answer": "ERROR IN THE ANSWER",
                    "contexts": [],
                    "ground_truth": item["expected_answer"],
                }

    tasks = [wrapped_rag_fn(item) for item in golden_set]
    results = await asyncio.gather(*tasks)

    dataset = Dataset.from_list(results)

    # configs LLM e Embeddings
    evaluator_llm = ChatOllama(model="llama3.1", temperature=0, timeout=240)
    evaluator_embeddings = OllamaEmbeddings(model="llama3.1")

    # max_workers=1 for better model performance
    run_config = RunConfig(max_workers=1, timeout=240)

    logger.info("Starting Ragas metrics calculation (Local Processing)...")
    
    result = evaluate(
        dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
        ],
        llm=evaluator_llm,
        embeddings=evaluator_embeddings,
        run_config=run_config
    )

    # auxiliary function for calculating the average, handling lists or direct values.
    def get_mean_score(res_obj, metric_name):
        val = res_obj[metric_name]
        if isinstance(val, list):
            # filter out NaNs to calculate the average only of what was correct.
            valid_vals = [v for v in val if v is not None and not np.isnan(v)]
            return float(np.mean(valid_vals)) if valid_vals else 0.0
        return float(val) if val is not None else 0.0

    metrics = {
        "faithfulness": get_mean_score(result, "faithfulness"),
        "answer_relevancy": get_mean_score(result, "answer_relevancy"),
        "context_precision": get_mean_score(result, "context_precision"),
        "context_recall": get_mean_score(result, "context_recall"),
    }

    logger.info("RAGAS final scores: %s", metrics)
    return metrics