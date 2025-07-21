import re
from typing import List, Dict, Any
from langchain_text_splitters import CharacterTextSplitter
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
import streamlit as st

class LegalDocumentProcessor:
    def __init__(self, chunk_size: int = 1500, chunk_overlap: int = 300):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = CharacterTextSplitter(
            separators="\n\n",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
    
    def load_pdf(self, file_path: str) -> List[Document]:
        """Load PDF and extract text with metadata"""
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        return documents
    
    def process_documents(self, documents: List[Document]) -> List[Document]:
        """Process documents with legal structure awareness"""
        processed_docs = []
        
        for doc in documents:
            # Split the document
            chunks = self.text_splitter.split_documents([doc])
            
            # Add enhanced metadata to each chunk
            for i, chunk in enumerate(chunks):
                metadata = {
                    'source': doc.metadata['source'][5:], # remove temp_ prefix
                    'page': int(doc.metadata.get('page', 0)),
                    'chunk_id': i
                }
                processed_docs.append(Document(page_content=chunk.page_content, metadata=metadata))
        
        return processed_docs
    
    def process_uploaded_file(self, uploaded_file) -> List[Document]:
        """Process uploaded Streamlit file"""
        # Save uploaded file temporarily
        with open(f"temp_{uploaded_file.name}", "wb") as f:
            f.write(uploaded_file.getvalue())
        
        # Load and process
        documents = self.load_pdf(f"temp_{uploaded_file.name}")
        processed_docs = self.process_documents(documents)
        
        # Clean up temp file
        import os
        os.remove(f"temp_{uploaded_file.name}")
        
        return processed_docs