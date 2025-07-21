import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = "gpt-4o"
    OPENAI_EMBEDDING_MODEL = "text-embedding-3-large"
    
    # Pinecone Configuration
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "legal-documents")
    
    # Document Processing
    CHUNK_SIZE = 1200
    CHUNK_OVERLAP = 250
    
    # RAG Configuration
    RETRIEVAL_TOP_K = 5
    RELEVANCE_THRESHOLD = 7.0
    MAX_RETRIEVAL_ATTEMPTS = 2
    
    # Database
    DATABASE_PATH = "database/faqs.db"
    
    # Streamlit Configuration
    PAGE_TITLE = "Legal AI Assistant"
    PAGE_ICON = "⚖️"

settings = Settings()