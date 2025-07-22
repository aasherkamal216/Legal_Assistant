# AI Legal Assistant

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)

A RAG-based AI Legal Assistant designed to provide tailored legal information from a private knowledge base. It features an adaptive user interface that tailors responses to different user types, a sophisticated retrieval-scoring-rewriting loop for accuracy, and automatic FAQ generation from user conversations.

## ✨ Key Features

*   **Interactive Chat Interface**: A user-friendly chat application built with Streamlit.
*   **Adaptive AI Persona**: The assistant adjusts its communication style and response depth for `Legal Professionals`, `Law Students`, and the `General Public`.
*   **Document Management Dashboard**: An interface to upload PDF documents, which are then processed, chunked, and stored in a vector knowledge base.
*   **Agentic RAG**: The system uses a `LangGraph`-powered agent that:
    1.  **Retrieves** relevant document chunks from a Pinecone vector store.
    2.  **Scores** the relevance of the retrieved context against the user's query.
    3.  **Rewrites** the query and re-retrieves if the initial results are not relevant enough.
*   **Automatic FAQ Generation**: After a chat session ends, a background process analyzes the conversation to generate and store relevant FAQs in a local SQLite database, improving the knowledge base over time.
*   **Pinecone Integration**: Leverages Pinecone for efficient and scalable vector similarity search.
*   **Modular & Extensible**: The codebase is organized into distinct modules for configuration, application logic, and core AI components.


## 🛠️ Technology Stack

*   **AI Frameworks**: LangChain, LangGraph
*   **LLM Provider**: OpenAI
*   **Vector Database**: Pinecone
*   **Web Framework**: Streamlit
*   **Data Storage**: SQLite (for FAQs)
*   **Dependencies**: See `pyproject.toml` for the full list.

## 📁 Project Structure

```
└── legal_assistant/
    ├── apps/                 # Streamlit applications
    │   ├── assistant.py      # Main chat interface
    │   └── dashboard.py      # Document management dashboard
    ├── config/               # Configuration files
    │   ├── database.py       # SQLite database handler for FAQs
    │   └── settings.py       # Project settings and API keys
    ├── src/                  # Core source code for the RAG pipeline
    │   ├── document_processor.py # Handles PDF loading and chunking
    │   ├── faq_generator.py  # Logic for generating FAQs from conversations
    │   ├── graph.py          # LangGraph agent definition
    │   ├── nodes.py          # Agent nodes (assistant, RAG loop)
    │   ├── prompts.py        # All system and task prompts
    │   ├── tools.py          # Custom tools for the agent (e.g., knowledge base search)
    │   └── vector_store.py   # Manages interaction with Pinecone
    ├── generate_faqs_task.py # Background script for FAQ generation
    ├── pyproject.toml        # Project dependencies
    ├── README.md             # You are here!
    └── .python-version       # Specifies Python version (3.11)
```

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### 1. Prerequisites

*   Python 3.11
*   An active OpenAI API key.
*   An active Pinecone API key and environment.

### 2. Installation

1.  **Set up a virtual environment:**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

2.  **Install the dependencies:**
    ```sh
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables:**
    Create a `.env` file in the project root directory by copying the example below.
    ```sh
    touch .env
    ```

    Add your API keys and Pinecone index name to the `.env` file:
    ```.env
    OPENAI_API_KEY="sk-..."
    PINECONE_API_KEY="..."
    PINECONE_INDEX_NAME="your-pinecone-index-name"
    ```

### 3. How to Run the Application

You need to run two separate Streamlit applications. It's recommended to run them in separate terminal tabs.

1.  **Run the Document Management Dashboard:**
    ```sh
    python -m streamlit run apps/dashboard.py
    ```
    Navigate to the URL provided by Streamlit (usually `http://localhost:8501`) to upload your documents.

2.  **Run the Legal Assistant Chat App:**
    ```sh
    python -m streamlit run apps/assistant.py
    ```
    Navigate to the URL provided (usually `http://localhost:8502` if the dashboard is still running) to interact with the assistant.

## ⚙️ How It Works

### RAG Chat Flow

The chat flow is managed by a `LangGraph` agent defined in `src/graph.py`.

1.  **Initial Call**: The user's query is sent to the `assistant_node`. The model, armed with the `search_knowledge_base` tool, determines that it needs to retrieve information and makes a tool call.
2.  **RAG Loop (`rag_node`)**:
    *   **Retrieve**: The `search_knowledge_base` tool (`src/tools.py`) is invoked, performing a similarity search in Pinecone.
    *   **Score**: The retrieved documents are scored for relevance against the original query using a dedicated model and prompt (`src/prompts.py`).
    *   **Rewrite (if needed)**: If the score is below a `RELEVANCE_THRESHOLD` (defined in `config/settings.py`), the system uses another model to rewrite the original query to be more specific or use better legal terminology. It then re-runs the retrieval. This loop can run up to `MAX_RETRIEVAL_ATTEMPTS`.
3.  **Generation**: Once relevant context is retrieved, it's passed back to the `assistant_node`. The main model then generates a final, comprehensive answer based on this context, tailored to the selected user type (`is_professional`).

### Automatic FAQ Generation

When a user ends a chat, the full conversation history is saved to a temporary JSON file. A non-blocking background process is launched, executing `generate_faqs_task.py`. This script:
1.  Loads the conversation history.
2.  Uses an LLM with a specialized prompt (`FAQ_PROMPT`) to identify key questions and answers.
3.  Parses the structured output and stores the new FAQs in the `database/faqs.db` SQLite database using `config/database.py`. Existing questions have their frequency count incremented.
4.  These FAQs are then displayed on the main welcome screen of the chat app.
