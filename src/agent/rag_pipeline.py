import os
from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

class RAGPipeline:
    def __init__(self, index_path="data/processed/vector_store"):
        self.index_path = index_path
        ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        
        # enbedding model
        self.embeddings = OllamaEmbeddings(
            model="mxbai-embed-large",
            base_url=ollama_base_url
        )
        self.vector_store = None
        
        if os.path.exists(index_path):
            try:
                self.vector_store = FAISS.load_local(
                    index_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
            except Exception as e:
                print(f"Error loading vector store: {e}")

    def ingest_documents(self, documents):
        """
        It receives a list of documents (Language Chain Document objects), it splits them into chunks and saves them in the vector database.
        """
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500, 
            chunk_overlap=50
        )
        chunks = text_splitter.split_documents(documents)
        
        self.vector_store = FAISS.from_documents(chunks, self.embeddings)
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        self.vector_store.save_local(self.index_path)
        return f"Ingestion completed: {len(chunks)} chunks created in {self.index_path}"

    def get_context(self, query, k=3):
        """Find the most relevant context for the query."""
        if not self.vector_store:
            return "Warning: No knowledge base loaded. Answer based on your general knowledge."
        
        docs = self.vector_store.similarity_search(query, k=k)
        context = "\n---\n".join([doc.page_content for doc in docs])
        return context
