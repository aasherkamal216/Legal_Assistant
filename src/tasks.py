from langgraph.func import task
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, BaseMessage, ToolMessage
from langchain_core.documents import Document
from langchain_openai import ChatOpenAI

from .tools import search_knowledge_base
from .prompts import (
    ASSISTANT_PROMPT_FOR_PROFESSIONALS,
    ASSISTANT_PROMPT_FOR_STUDENTS,
    SCORE_PROMPT,
    REWRITE_PROMPT,
)

from pydantic import BaseModel, Field
from config.settings import settings

model = ChatOpenAI(model=settings.PRIMARY_MODEL, api_key=settings.OPENAI_API_KEY)
scoring_model = ChatOpenAI(
    model=settings.SCORE_DOCUMENTS_MODEL,
    api_key=settings.OPENAI_API_KEY,
    temperature=0.5,
)
rewriter_model = ChatOpenAI(
    model=settings.REWRITE_QUERY_MODEL, api_key=settings.OPENAI_API_KEY, temperature=0.5
)

agent_with_tool = model.bind_tools([search_knowledge_base])

###########################
# Main Assistant
###########################
@task
def assistant(
    messages: list[BaseMessage],
    is_professional: bool
) -> AIMessage:
    """Decide whether to answer or retrieve documents."""

    response = agent_with_tool.invoke(
        [
            SystemMessage(
                content=ASSISTANT_PROMPT_FOR_PROFESSIONALS if is_professional else ASSISTANT_PROMPT_FOR_STUDENTS
            )
        ] + messages
    )
    return response


###########################
# Retrieve Documents
###########################
@task
def retrieve(tool_call: dict) -> str:
    """Retrieve documents based on the AI message's tool call."""

    retrieved_context = search_knowledge_base.invoke(tool_call["args"])
    return ToolMessage(content=retrieved_context, tool_call_id=tool_call["id"])


###########################
# Score Documents
###########################
class ScoreDocument(BaseModel):
    score: int = Field(..., description="Score for the documents (combined) from 1-10 for a given query.", ge=1, le=10)

@task
def score_documents(
    query: str,
    context: str
) -> int:
    """Score the retrieved documents

    Args:
        query (str): The user's query.
        context (str): The retrieved documents.
    Returns:
        int: The score for the context.
    """

    prompt = SCORE_PROMPT.format(query=query, context=context)
    response = (
        scoring_model
        .with_structured_output(ScoreDocument)
        .invoke([HumanMessage(content=prompt)])
    )

    return response.score


###########################
# Rewrite Query
###########################
class ModifiedQuery(BaseModel):
    query: str = Field(..., description="The enhanced query to search into the vector store.")

@task
def rewrite_query(
    query: str,
) -> str:
    """Rewrite the original search query."""

    prompt = REWRITE_PROMPT.format(query=query)
    response = (
        rewriter_model
        .with_structured_output(ModifiedQuery)
        .invoke([HumanMessage(content=prompt)])
    )

    return response.query
