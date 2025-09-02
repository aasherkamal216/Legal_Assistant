from langgraph.graph import StateGraph, MessagesState, END

# Import the node functions directly
from .nodes import assistant_node, rag_node

# 1. Define the State for our graph
class AgentState(MessagesState):
    is_professional: bool

# 2. Define the conditional edge logic
def should_continue(state: AgentState) -> str:
    """Determines the next step after the assistant node."""
    last_message = state['messages'][-1]
    if last_message.tool_calls:
        return "perform_rag"
    else:
        return END

# 3. Build and compile the graph
def create_legal_assistant_graph():
    workflow = StateGraph(AgentState)

    # Add the nodes directly
    workflow.add_node("assistant", assistant_node)
    workflow.add_node("rag_loop", rag_node)

    workflow.set_entry_point("assistant")
    
    workflow.add_conditional_edges(
        "assistant",
        should_continue,
        {
            "perform_rag": "rag_loop",
            END: END,
        },
    )
    workflow.add_edge("rag_loop", "assistant")

    return workflow.compile()

# Instantiate the graph for use in the Streamlit app
legal_assistant = create_legal_assistant_graph()