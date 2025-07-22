import os
from dotenv import load_dotenv

_ = load_dotenv()

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    PRIMARY_MODEL = "gpt-4o-mini"
    REWRITE_QUERY_MODEL = "gpt-4o-mini"
    SCORE_DOCUMENTS_MODEL = "gpt-4o-mini"
    EMBEDDING_MODEL = "text-embedding-3-large"
    
    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "legal-documents")
    
    # Document Processing
    CHUNK_SIZE = 1200
    CHUNK_OVERLAP = 250
    
    # RAG Configuration
    RETRIEVAL_TOP_K = 5
    RELEVANCE_THRESHOLD = 7
    MAX_RETRIEVAL_ATTEMPTS = 2
    
    PINECONE_FAQ_NAMESPACE = "faq-questions"

    # Streamlit Configuration
    PAGE_TITLE = "Legal AI Assistant"
    PAGE_ICON = "⚖️"

settings = Settings()