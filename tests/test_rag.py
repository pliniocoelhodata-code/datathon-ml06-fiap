import os
import shutil
import pytest
from langchain_core.documents import Document
from src.agent.rag_pipeline import RAGPipeline

@pytest.fixture
def temp_rag_path():
    """Creates a temporary path to the test vector database."""
    path = "data/processed/test_vector_store"
    if os.path.exists(path):
        shutil.rmtree(path)
    yield path
    if os.path.exists(path):
        shutil.rmtree(path)

def test_rag_ingestion_and_retrieval(temp_rag_path):
    rag = RAGPipeline(index_path=temp_rag_path)
    
    # 1. Test Intake
    sample_docs = [
        Document(page_content="PETR4 fechou a R$ 38,50 com IFR em 25.", metadata={"source": "test"}),
        Document(page_content="O IFR abaixo de 30 indica zona de sobrevenda.", metadata={"source": "test"})
    ]
    
    result = rag.ingest_documents(sample_docs)
    assert "Ingestão concluída" in result
    assert os.path.exists(temp_rag_path)

    # 2. Test Recovery (Retrieval)
    new_rag = RAGPipeline(index_path=temp_rag_path)
    query = "O que significa o IFR da PETR4?"
    context = new_rag.get_context(query, k=1)
    
    assert "PETR4" in context or "IFR" in context
    assert isinstance(context, str)
