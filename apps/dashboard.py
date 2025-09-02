import streamlit as st
import os
from ..src.document_processor import LegalDocumentProcessor
from ..src.vector_store import VectorStoreManager
from config.settings import settings

def main():
    st.set_page_config(
        page_title="Document Dashboard",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Document Management Dashboard")
    st.markdown("---")
    
    # Initialize components
    if 'doc_processor' not in st.session_state:
        st.session_state.doc_processor = LegalDocumentProcessor(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP
        )
    
    if 'vector_store' not in st.session_state:
        st.session_state.vector_store = VectorStoreManager()
    
    # Main dashboard
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📄 Upload Documents")
        
        # File uploader
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=['pdf'],
            accept_multiple_files=True,
            help="Upload legal documents (PDFs) to add to the knowledge base"
        )

        
        # Process button
        if st.button("Process Documents", type="primary", disabled=not uploaded_files):
            if uploaded_files:
                process_documents(uploaded_files)
    
    with col2:
        st.header("⚙️ Dashboard Controls")
        
        # Statistics
        st.subheader("📊 Statistics")
        st.metric("Documents Processed", st.session_state.get('docs_processed', 0))
        st.metric("Total Chunks", st.session_state.get('total_chunks', 0))
        
        st.markdown("---")
        
    # Processing status
    if 'processing_status' in st.session_state:
        st.markdown("---")
        st.subheader("📋 Processing Status")
        for status in st.session_state.processing_status:
            st.write(status)

def process_documents(uploaded_files):
    """Process uploaded documents"""
    st.session_state.processing_status = []
    
    status_text = st.empty()
    
    all_documents = []
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")
        
        try:
            # Process document
            documents = st.session_state.doc_processor.process_uploaded_file(uploaded_file)
            all_documents.extend(documents)
            
            st.session_state.processing_status.append(
                f"✅ {uploaded_file.name}: {len(documents)} chunks processed"
            )
            
        except Exception as e:
            st.session_state.processing_status.append(
                f"❌ {uploaded_file.name}: Error - {str(e)}"
            )
            st.error(f"Error processing {uploaded_file.name}: {str(e)}")
    
    # Store all documents in vector store
    if all_documents:
        status_text.text("Storing documents in vector database...")
        if st.session_state.vector_store.store_documents(all_documents):
            st.success(f"Successfully processed and stored {len(all_documents)} document chunks!")
            
            # Update statistics
            st.session_state.docs_processed = st.session_state.get('docs_processed', 0) + len(uploaded_files)
            st.session_state.total_chunks = st.session_state.get('total_chunks', 0) + len(all_documents)
            
        else:
            st.error("Failed to store documents in vector database!")

    status_text.text("Processing complete!")

if __name__ == "__main__":
    main()