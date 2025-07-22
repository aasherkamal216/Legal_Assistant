import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from src.graph import legal_assistant
from src.vector_store import VectorStoreManager
import subprocess
import json
import os
import uuid
import sys

# Page configuration
st.set_page_config(
    page_title="Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize VectorStoreManager once using Streamlit's cache
@st.cache_resource
def get_vector_store_manager():
    return VectorStoreManager()

vector_store_manager = get_vector_store_manager()

def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_type" not in st.session_state:
        st.session_state.user_type = None
    if "is_professional" not in st.session_state:
        st.session_state.is_professional = None
    if "prompt_from_button" not in st.session_state:
        st.session_state.prompt_from_button = None

def reset_conversation():
    """Reset the conversation and user type"""
    st.session_state.messages = []
    st.session_state.user_type = None
    st.session_state.is_professional = None
    st.rerun()

def trigger_question_generation():
    """Saves the conversation and triggers the background question generation script."""
    if not st.session_state.get("messages") or len(st.session_state.messages) < 2:
        st.toast("Conversation is too short for analysis.", icon="INFO")
        return

    conversation_history = [
        {"role": "user" if isinstance(msg, HumanMessage) else "assistant", "content": msg.content}
        for msg in st.session_state.messages
    ]

    temp_dir = "temp_conversations"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"conv_{uuid.uuid4()}.json")
    with open(file_path, 'w') as f:
        json.dump(conversation_history, f)
        
    script_path = "generate_questions_task.py"
    command = [sys.executable, script_path, file_path]
    
    try:
        subprocess.Popen(command)
        st.toast("Thanks for your chat! We'll use it to improve future suggestions.", icon="✅")
    except Exception as e:
        st.error(f"Failed to start background task: {e}")

def reset_conversation():
    """Reset the conversation and user type"""
    st.session_state.messages = []
    st.session_state.user_type = None
    st.session_state.is_professional = None
    st.session_state.prompt_from_button = None
    st.rerun()

def end_chat_and_reset():
    """Trigger generation and then reset."""
    trigger_question_generation()
    reset_conversation()

def user_type_selection():
    """Display user type selection interface"""
    st.title("⚖️ Legal Assistant")
    st.markdown("---")
    st.markdown("### Welcome to your AI Legal Assistant!\nPlease select your background to get the most appropriate assistance:")
    col1, col2, col3 = st.columns(3)
    if col1.button("🎓 Legal Professional", use_container_width=True):
        st.session_state.user_type, st.session_state.is_professional = "Legal Professional", True
        st.rerun()
    if col2.button("📚 Law Student", use_container_width=True):
        st.session_state.user_type, st.session_state.is_professional = "Law Student", False
        st.rerun()
    if col3.button("👤 General Public", use_container_width=True):
        st.session_state.user_type, st.session_state.is_professional = "General Public", False
        st.rerun()
    st.markdown("---")


def handle_button_click(question: str):
    """Callback function to set the next prompt from a button click."""
    st.session_state.prompt_from_button = question

def display_chat_interface():
    """Display the main chat interface"""
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("⚖️ Legal Assistant")
    if col2.button("🔄 Change User Type", use_container_width=True):
        reset_conversation()
    if col3.button("🔚 End Chat", use_container_width=True, help="End this chat and help improve the assistant"):
        end_chat_and_reset()

    for message in st.session_state.messages:
        with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
            st.write(message.content)
            if isinstance(message, AIMessage) and "related_questions" in message.additional_kwargs:
                questions = message.additional_kwargs["related_questions"]
                if questions:
                    st.markdown("**Related Questions:**")
                    for i, q in enumerate(questions):
                        button_key = f"related_{message.id}_{i}"
                        if st.button(q, key=button_key, on_click=handle_button_click, args=(q,), use_container_width=True):
                            pass
    
    prompt = st.session_state.pop('prompt_from_button', None) or st.chat_input("Ask your legal question...")

    if prompt:
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.rerun()
    
    # Process the last message if it's from the user
    if st.session_state.messages and isinstance(st.session_state.messages[-1], HumanMessage):
        last_user_message = st.session_state.messages[-1]
        
        with st.chat_message("assistant"):
            try:
                graph_input = {
                    "messages": st.session_state.messages,
                    "is_professional": st.session_state.is_professional
                }
                def stream_generator(input_data):
                    for chunk, metadata in legal_assistant.stream(input_data, stream_mode="messages"):
                        if metadata.get("langgraph_node") == "assistant" and chunk.content:
                            yield chunk.content
                
                full_response = st.write_stream(stream_generator(graph_input))
                
                related_questions = vector_store_manager.get_similar_faq_questions(last_user_message.content, k=3)
                
                assistant_message = AIMessage(
                    content=full_response,
                    additional_kwargs={"related_questions": related_questions}
                )
                st.session_state.messages.append(assistant_message)
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")


def add_sidebar():
    """Add sidebar with additional information"""
    with st.sidebar:
        st.header("ℹ️ Information")
        st.markdown(f"""
        **Current Session:**
        - User Type: {st.session_state.user_type}
        - Messages: {len(st.session_state.messages)}
        """)
        st.markdown("---")
        st.markdown("""
        **Disclaimer:**
        This AI assistant provides general legal information and should not be considered as legal advice. 
        For specific legal matters, please consult with a qualified attorney.
        """)
        st.markdown("---")
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()


def main():
    """Main application function"""
    initialize_session_state()
    if st.session_state.user_type is None:
        user_type_selection()
    else:
        add_sidebar()
        display_chat_interface()

if __name__ == "__main__":
    main()