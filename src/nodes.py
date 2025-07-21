# tasks.py (Refactored)

from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from .tools import search_knowledge_base
from .prompts import (
    ASSISTANT_PROMPT_FOR_PROFESSIONALS,
    ASSISTANT_PROMPT_FOR_STUDENTS,
    SCORE_PROMPT,
    REWRITE_PROMPT,
)
from config.settings import settings

# --- Initialize Models (No changes) ---
model = ChatOpenAI(model=settings.PRIMARY_MODEL, api_key=settings.OPENAI_API_KEY)
scoring_model = ChatOpenAI(model=settings.SCORE_DOCUMENTS_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.5)
rewriter_model = ChatOpenAI(model=settings.REWRITE_QUERY_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.5)

agent_with_tool = model.bind_tools([search_knowledge_base])

# --- Pydantic Models for Structured Output (No changes) ---
class ScoreDocument(BaseModel):
    score: int = Field(..., description="Score for the documents (combined) from 1-10 for a given query.", ge=1, le=10)

class ModifiedQuery(BaseModel):
    query: str = Field(..., description="The enhanced query to search into the vector store.")

# --- Helper functions for the RAG node ---
def _retrieve(tool_call: dict) -> ToolMessage:
    retrieved_context = search_knowledge_base.invoke(tool_call["args"])
    return ToolMessage(content=retrieved_context, tool_call_id=tool_call["id"])

def _score_documents(query: str, context: str) -> int:
    prompt = SCORE_PROMPT.format(query=query, context=context)
    response = scoring_model.with_structured_output(ScoreDocument).invoke([HumanMessage(content=prompt)])
    return response.score

def _rewrite_query(query: str) -> str:
    prompt = REWRITE_PROMPT.format(query=query)
    response = rewriter_model.with_structured_output(ModifiedQuery).invoke([HumanMessage(content=prompt)])
    return response.query



def assistant_node(state) -> dict:
    """
    This is the primary node that calls the main LLM.
    It checks for tool calls and returns the AI message.
    """
    messages = state['messages']
    is_professional = state['is_professional']
    
    system_prompt = ASSISTANT_PROMPT_FOR_PROFESSIONALS if is_professional else ASSISTANT_PROMPT_FOR_STUDENTS
    response = agent_with_tool.invoke([SystemMessage(content=system_prompt)] + messages)
    
    # The output of a node must be a dictionary that updates the state
    return {"messages": [response]}

def rag_node(state) -> dict:
    """
    This node performs the RAG loop: retrieve, score, and rewrite if necessary.
    """
    messages = state['messages']
    # Find the original user query
    human_message = next(msg for msg in reversed(messages) if isinstance(msg, HumanMessage))
    
    last_ai_message = messages[-1]
    tool_calls = last_ai_message.tool_calls
    
    loop_count = 0
    while loop_count < 2:
        # Use the helper function to retrieve documents
        retrieved_docs_msg = _retrieve(tool_calls[-1])
        
        # Use the helper function to score
        score = _score_documents(
            query=human_message.content, 
            context=retrieved_docs_msg.content
        )

        if score < settings.RELEVANCE_THRESHOLD:
            # Use the helper function to rewrite
            enhanced_query = _rewrite_query(tool_calls[-1]["args"]["query"])
            tool_calls[-1]["args"]["query"] = enhanced_query
            loop_count += 1
            continue
        else:
            # If score is good, break and return the successful retrieval
            return {"messages": [retrieved_docs_msg]}
            
    # If the loop finishes, return the last attempt's retrieval
    return {"messages": [retrieved_docs_msg]}