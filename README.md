# AI Legal Assistant

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)

A RAG-based AI Legal Assistant designed to provide tailored legal information from a private knowledge base. It features an adaptive user interface that tailors responses to different user types, a sophisticated retrieval-scoring-rewriting loop for accuracy, and dynamic question suggestions to guide user exploration.

## ✨ Key Features

*   **Interactive Chat Interface**: A user-friendly chat application built with Streamlit.
*   **Adaptive AI Persona**: The assistant adjusts its communication style and response depth for `Legal Professionals`, `Law Students`, and the `General Public`.
*   **Document Management Dashboard**: An interface to upload PDF documents, which are then processed, chunked, and stored in a vector knowledge base.
*   **Agentic RAG**: The system uses a `LangGraph`-powered agent that:
    1.  **Retrieves** relevant document chunks from a Pinecone vector store.
    2.  **Scores** the relevance of the retrieved context against the user's query.
    3.  **Rewrites** the query and re-retrieves if the initial results are not relevant enough.
*   **Dynamic "Related Questions"**: After each response, the assistant suggests similar questions stored in the vector database, guiding users to explore related topics.
*   **Conversation-Driven Question Generation**: After a chat session ends, a background process analyzes the conversation to generate new, relevant questions, which are added to Pinecone to improve future suggestions.
*   **Pinecone Integration**: Leverages Pinecone for both the primary knowledge base and the storage/retrieval of suggested questions.
*   **Modular & Extensible**: The codebase is organized into distinct modules for configuration, application logic, and core AI components.


## 🛠️ Technology Stack

*   **AI Frameworks**: LangChain, LangGraph
*   **LLM Provider**: OpenAI
*   **Vector Database**: Pinecone (for knowledge base and question suggestions)
*   **Web Framework**: Streamlit
*   **Dependencies**: See `pyproject.toml` or `requirements.txt` for the full list.

## 📁 Project Structure

```
└── legal_assistant/
    ├── apps/                 # Streamlit applications
    │   ├── assistant.py      # Main chat interface
    │   └── dashboard.py      # Document management dashboard
    ├── config/               # Configuration files
    │   └── settings.py       # Project settings and API keys
    ├── src/                  # Core source code for the RAG pipeline
    │   ├── document_processor.py # Handles PDF loading and chunking
    │   ├── graph.py          # LangGraph agent definition
    │   ├── nodes.py          # Agent nodes (assistant, RAG loop)
    │   ├── prompts.py        # All system and task prompts
    │   ├── question_generator.py # Logic for generating suggested questions from conversations
    │   ├── tools.py          # Custom tools for the agent (e.g., knowledge base search)
    │   └── vector_store.py   # Manages interaction with Pinecone
    ├── generate_questions_task.py # Background script for question generation
    ├── pyproject.toml        # Project metadata and dependencies
    ├── requirements.txt      # Pinned dependencies for reproducible environments
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

3.  **Configure Environment Variables:**
    Create a `.env` file in the project root directory.
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
    *   **Retrieve**: The `search_knowledge_base` tool (`src/tools.py`) is invoked, performing a similarity search in Pinecone's default namespace.
    *   **Score**: The retrieved documents are scored for relevance against the original query using a dedicated model and prompt (`src/prompts.py`).
    *   **Rewrite (if needed)**: If the score is below a `RELEVANCE_THRESHOLD` (defined in `config/settings.py`), the system uses another model to rewrite the original query to be more specific. It then re-runs the retrieval. This loop can run up to `MAX_RETRIEVAL_ATTEMPTS`.
3.  **Generation**: Once relevant context is retrieved, it's passed back to the `assistant_node`. The main model then generates a final, comprehensive answer based on this context, tailored to the selected user type.

### Dynamic "Related Questions" Feature

To guide users, the assistant displays relevant follow-up questions.
1.  After the RAG pipeline generates an answer, the `assistant.py` app takes the user's most recent query.
2.  It performs a vector similarity search against a dedicated `faq-questions` namespace in Pinecone using `vector_store.get_similar_faq_questions()`.
3.  The top matching questions are displayed to the user as clickable buttons, providing an intuitive way to explore related topics.

### Conversation-Driven Question Generation

The system improves its question suggestion capability by learning from user interactions.
1.  When a user ends a chat, `assistant.py` saves the conversation history to a temporary JSON file.
2.  A non-blocking background process is launched, executing `generate_questions_task.py`.
3.  This script loads the conversation and uses the `QuestionGenerator` (`src/question_generator.py`) with a specialized prompt (`SUGGESTED_QUESTIONS_PROMPT`) to formulate new, relevant questions.
4.  The `VectorStoreManager` then vectorizes these questions and adds them to the `faq-questions` namespace in the Pinecone index, making them available for future user sessions.
