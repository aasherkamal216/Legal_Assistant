from typing import List, Optional
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from config.settings import settings
import streamlit as st
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VectorStoreManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.index_name = settings.PINECONE_INDEX_NAME
        self.faq_namespace = settings.PINECONE_FAQ_NAMESPACE
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Check if index exists, create if not
        if self.index_name not in pc.list_indexes().names():
            logger.info(f"Creating Pinecone index: {self.index_name}")
            pc.create_index(
                name=self.index_name,
                dimension=3072, # Dimension for text-embedding-3-large
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
        else:
            logger.info(f"Pinecone index '{self.index_name}' already exists.")

    def store_documents(self, documents: List[Document]) -> bool:
        """Store documents in Pinecone vector store (default namespace)"""
        try:
            PineconeVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=self.index_name
            )
            return True
        except Exception as e:
            st.error(f"Error storing documents: {str(e)}")
            return False
    
    def get_vector_store(self, namespace: Optional[str] = None) -> PineconeVectorStore:
        """Get Pinecone vector store instance for a given namespace."""
        return PineconeVectorStore(
            index_name=self.index_name,
            embedding=self.embeddings,
            namespace=namespace
        )

    def add_suggested_questions(self, questions: List[str]):
        """Adds a list of questions to the suggestion namespace in Pinecone."""
        if not questions:
            return
        try:
            faq_vector_store = self.get_vector_store(namespace=self.faq_namespace)
            faq_vector_store.add_texts(questions)
            logger.info(f"Stored {len(questions)} suggested questions.")
        except Exception as e:
            logger.error(f"Failed to add suggested questions to Pinecone: {e}")

    def get_similar_faq_questions(self, query: str, k: int = 3) -> List[str]:
        """Searches for similar questions in the FAQ namespace."""
        if not query:
            return []
        try:
            faq_vector_store = self.get_vector_store(namespace=self.faq_namespace)
            results = faq_vector_store.similarity_search(query, k=k)
            similar_questions = [doc.page_content for doc in results]
            logger.info(f"Found {len(similar_questions)} similar questions for query: '{query}'")
            return similar_questions
        except Exception as e:
            logger.error(f"Failed to retrieve similar FAQ questions from Pinecone: {e}")
            return []