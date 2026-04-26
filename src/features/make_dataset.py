import json
import os
from langchain_core.documents import Document
from src.agent.rag_pipeline import RAGPipeline
import yfinance as yf
import os
import yaml

def ingest_golden_set(json_path="data/golden_set/sample.json"):
    """
    Reads the Golden Set file and indexes the content in the RAG Vector Store.
    Transforms the Golden Set's technical knowledge into a query database for the Agent.
    """
    if not os.path.exists(json_path):
        print(f"Error: File {json_path} not found.")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading JSON: {e}")
        return

    documents = []
    for item in data:
        content = (
            f"Topic: {item['category']}\n"
            f"Technical Information: {item['expected_answer']}\n"
            f"Related Context: {item['context']}"
        )
        
        doc = Document(
            page_content=content,
            metadata={
                "id": item["id"],
                "category": item["category"],
                "source": "golden_set"
            }
        )
        documents.append(doc)

    print(f"Documents to process: {len(documents)}")
    
    # Inicializa o pipeline e salva na pasta data/processed/vector_store
    try:
        rag = RAGPipeline()
        result = rag.ingest_documents(documents)
        print(f"Success: {result}")
    except Exception as e:
        print(f"Error during ingestion: {e}")

def download_data():
    with open('configs/model_config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    symbol = config['data']['symbol']
    path = config['data']['raw_path']
    
    df = yf.download(symbol, period="1y", progress=False)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path)
    print(f"Saved data in: {path}")

if __name__ == "__main__":
    os.makedirs("data/processed", exist_ok=True)
    ingest_golden_set()
    # download_data()
