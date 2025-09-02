from langchain_core.tools import tool
from langchain_core.documents import Document

from src.vector_store import VectorStoreManager
from config.settings import settings

vector_store_manager = VectorStoreManager()

def _format_docs(docs: list[Document]) -> str:
    formatted_docs = "\n\n---\n\n".join(
        [
            f'<Document source="{doc.metadata["source"]}" page="{doc.metadata["page"]}" chunk_id="{doc.metadata["chunk_id"]}">\n{doc.page_content}\n</Document>'
            for i, doc in enumerate(docs)
        ]
    )
    return formatted_docs


# Tool to search knowledge base
@tool
def search_knowledge_base(query: str, limit: int = settings.RETRIEVAL_TOP_K, source: str = None) -> str:
    """
    Searches the knowledgebase for relevant legal documents.
    Args:
        query (str): A detailed, descriptive query in **English language**.
        limit (int, optional): Number of Documents to retrieve. Defaults to 5.
        source (str, optional): A file name used to filter results 
            to only include results from that source document. e.g., 'MEDICINES and RELATED PRODUCTS ACT_2014.pdf'

    Returns:
        str: A string representation of the retrieved documents, 
            each wrapped in a `<Document>` XML tag
    """
    vector_store = vector_store_manager.get_vector_store()
    documents = vector_store.similarity_search(
        query, 
        k=limit,
        filter={"source": source} if source else None
    )
    
    return _format_docs(documents)