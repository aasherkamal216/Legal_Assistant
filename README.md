# AI Legal Assistant

[![Python Version](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/downloads/release/python-3110/)

A RAG-based AI Legal Assistant designed to provide tailored legal information from a private knowledge base. It features an adaptive user interface, a sophisticated retrieval-scoring-rewriting loop for accuracy, dynamic question suggestions, and a self-improving FAQ system.

## ✨ Key Features

*   **Interactive Chat Interface**: A user-friendly chat application built with Streamlit.
*   **Adaptive AI Persona**: The assistant adjusts its communication style and response depth for `Legal Professionals`, `Law Students`, and the `General Public`.
*   **Document Management Dashboard**: An interface to upload PDF documents, which are then processed, chunked, and stored in a vector knowledge base.
*   **Agentic RAG**: The system uses a `LangGraph`-powered agent that:
    1.  **Retrieves** relevant document chunks from a Pinecone vector store.
    2.  **Scores** the relevance of the retrieved context against the user's query.
    3.  **Rewrites** the query and re-retrieves if the initial results are not relevant enough.
*   **Dynamic "Related Questions"**: After each response, the assistant suggests similar questions from a vector database, displayed in the sidebar to guide user exploration.
*   **Conversation-Driven Content Generation**: When a user ends a chat, a unified background process is triggered to:
    *   **Generate FAQs**: Analyzes the conversation to create and store detailed Q&A pairs in a local SQLite database.
    *   **Generate Suggested Questions**: Creates new, concise questions and adds them to Pinecone to improve future suggestions.
*   **FAQ Page**: A dedicated page to browse all generated FAQs, categorized for easy access.
*   **Dual Database System**:
    *   **Pinecone**: For the primary knowledge base and for storing suggested questions.
    *   **SQLite**: For persisting structured FAQs.
*   **Modular & Extensible**: The codebase is organized into distinct modules for configuration, application logic, and core AI components.


## 🛠️ Technology Stack

*   **AI Frameworks**: LangChain, LangGraph
*   **LLM Provider**: OpenAI
*   **Vector Database**: Pinecone
*   **Structured Database**: SQLite
*   **Web Framework**: Streamlit
*   **Dependencies**: See `pyproject.toml` for the full list.

## 📁 Project Structure

```
└── legal_assistant/
    ├── apps/                 # Streamlit applications
    │   ├── assistant.py      # Main chat interface
    │   └── dashboard.py      # Document management dashboard
    ├── config/               # Configuration files
    │   ├── database.py       # Manages SQLite FAQ database
    │   └── settings.py       # Project settings and API keys
    ├── src/                  # Core source code for the RAG pipeline
    │   ├── document_processor.py # Handles PDF loading and chunking
    │   ├── faq_generator.py  # Logic for generating FAQs from conversations
    │   ├── graph.py          # LangGraph agent definition
    │   ├── nodes.py          # Agent nodes (assistant, RAG loop)
    │   ├── prompts.py        # All system and task prompts
    │   ├── question_generator.py # Logic for generating suggested questions
    │   ├── tools.py          # Custom tools for the agent (e.g., knowledge base search)
    │   └── vector_store.py   # Manages interaction with Pinecone
    ├── generate_content_task.py # Unified background script for all content generation
    ├── pyproject.toml        # Project metadata and dependencies
    ├── README.md             # You are here!
    └── .python-version       # Specifies Python version (3.11)
```

## 🚀 Getting Started

Follow these instructions to set up and run the project locally.

### 1. Prerequisites

*   Python 3.11
*   An active OpenAI API key.
*   An active Pinecone API key.

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

You can run two separate Streamlit applications. It's recommended to run them in separate terminal tabs.

1.  **Run the Document Management Dashboard:**
    ```sh
    python -m streamlit run apps/dashboard.py
    ```
    Navigate to the URL provided by Streamlit (usually `http://localhost:8501`) to upload your documents. This step is crucial for populating the knowledge base.

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
    *   **Score**: The retrieved documents are scored for relevance against the user's query using a dedicated model and prompt.
    *   **Rewrite (if needed)**: If the score is below a `RELEVANCE_THRESHOLD`, the system uses another model to rewrite the query for better results. It then re-runs the retrieval. This loop can run up to `MAX_RETRIEVAL_ATTEMPTS`.
3.  **Generation**: Once relevant context is retrieved, it's passed back to the `assistant_node`. The main model then generates a final, comprehensive answer based on this context, tailored to the selected user type.

### Self-Improving Content System

The assistant improves over time by learning from user conversations.

1.  **Trigger**: When a user clicks "End Chat", `assistant.py` saves the conversation history to a temporary file and launches the `generate_content_task.py` script in a non-blocking background process.
2.  **Dual Generation**: This unified script performs two tasks:
    *   **Suggested Questions**: It uses the `QuestionGenerator` to create a list of concise, related questions. These are vectorized and stored in a dedicated `faq-questions` namespace in Pinecone, making them available for the "Related Questions" feature in the sidebar.
    *   **FAQ Generation**: It uses the `FAQGenerator` to create detailed Question/Answer pairs based on the conversation. These are stored in a local SQLite database and can be viewed on the "Frequently Asked Questions" page.