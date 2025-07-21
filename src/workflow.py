from langgraph.func import entrypoint
from langchain_core.messages import BaseMessage, ToolMessage, HumanMessage
from langgraph.graph.message import add_messages

from .tasks import (
    assistant,
    retrieve,
    score_documents,
    rewrite_query,
)

from config.settings import settings
from pydantic import BaseModel


@entrypoint()
def legal_assistant(assistant_input: dict):
    messages = assistant_input["messages"]
    is_professional = assistant_input["is_professional"]

    human_message: HumanMessage = messages[-1]
    response = assistant(messages, is_professional).result()
    tool_calls = response.tool_calls
    loop_count = 0

    if tool_calls:
        while loop_count < 2:
            
            retrieved_docs: ToolMessage = retrieve(tool_calls[-1]).result()
            score: int = score_documents(query=human_message.content, context=retrieved_docs.content).result()

            if score < settings.RELEVANCE_THRESHOLD :
                enhanced_query: str = rewrite_query(tool_calls[-1]["args"]["query"]).result()
                tool_calls[-1]["args"]["query"] = enhanced_query

                loop_count += 1
                # Skip the iteration as context is not relevant (score too low)
                continue
            else:
                break
            
        # Append to message list
        messages = add_messages(messages, [response, retrieved_docs])

        final_response = assistant(messages, is_professional).result()
        return final_response

    return response