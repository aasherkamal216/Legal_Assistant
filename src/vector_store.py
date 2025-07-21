from typing import List, Optional
from langchain.schema import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from config.settings import settings
import streamlit as st

class VectorStoreManager:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model=settings.EMBEDDING_MODEL,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self._initialize_pinecone()
    
    def _initialize_pinecone(self):
        """Initialize Pinecone client and index"""
        pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        
        # Check if index exists, create if not
        if not pc.has_index(settings.PINECONE_INDEX_NAME):
            pc.create_index(
                name=settings.PINECONE_INDEX_NAME,
                dimension=3072,
                spec=ServerlessSpec(cloud="aws", region="us-east-1")
            )
    
    def store_documents(self, documents: List[Document]) -> bool:
        """Store documents in Pinecone vector store"""
        try:
            vector_store = PineconeVectorStore.from_documents(
                documents=documents,
                embedding=self.embeddings,
                index_name=settings.PINECONE_INDEX_NAME
            )
            return True
        except Exception as e:
            st.error(f"Error storing documents: {str(e)}")
            return False
    
    def get_vector_store(self) -> PineconeVectorStore:
        """Get Pinecone vector store instance"""
        return PineconeVectorStore(
            index_name=settings.PINECONE_INDEX_NAME,
            embedding=self.embeddings
        )