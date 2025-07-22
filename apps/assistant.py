import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from src.graph import legal_assistant
import subprocess
import json
import os
import uuid
import sys
from config.database import FAQDatabase
from config.settings import settings

# Page configuration
st.set_page_config(
    page_title="Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
def initialize_session_state():
    """Initialize session state variables"""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "user_type" not in st.session_state:
        st.session_state.user_type = None
    if "is_professional" not in st.session_state:
        st.session_state.is_professional = None

def reset_conversation():
    """Reset the conversation and user type"""
    st.session_state.messages = []
    st.session_state.user_type = None
    st.session_state.is_professional = None
    st.rerun()

def trigger_faq_generation():
    """
    Saves the conversation to a temp file and triggers the background FAQ generation script.
    """
    if "messages" not in st.session_state or len(st.session_state.messages) < 2:
        st.toast("Conversation is too short to generate FAQs.", icon=":material/info:")
        return

    # 1. Format conversation history into a serializable format
    conversation_history = []
    for msg in st.session_state.messages:
        if isinstance(msg, HumanMessage):
            role = "user"
            content = msg.content
        elif isinstance(msg, AIMessage):
            role = "assistant"
            content = msg.content
        else:
            continue  # Skip other message types
        conversation_history.append({"role": role, "content": content})

    # 2. Save to a temporary JSON file in a dedicated folder
    temp_dir = "temp_conversations"
    os.makedirs(temp_dir, exist_ok=True)
    file_path = os.path.join(temp_dir, f"conv_{uuid.uuid4()}.json")
    with open(file_path, 'w') as f:
        json.dump(conversation_history, f)
        
    # 3. Trigger background script using subprocess.Popen for non-blocking execution
    script_path = "generate_faqs_task.py"
    command = [sys.executable, script_path, file_path]
    
    try:
        subprocess.Popen(command)
        st.toast("Thank you! Your feedback will help improve our FAQs.", icon="✅")
    except FileNotFoundError:
        st.error(f"Error: Could not find the script '{script_path}'. Ensure it's in the project root.")
    except Exception as e:
        st.error(f"Failed to start background FAQ generation: {e}")

def display_faqs():
    """Fetches and displays FAQs from the database using expanders."""
    st.markdown("---")
    st.subheader("💡 Frequently Asked Questions")
    
    db_path = settings.DATABASE_PATH
    db_dir = os.path.dirname(db_path)

    # The FAQDatabase class creates the directory, but we check for the file
    # to avoid errors on first run and to show a helpful message.
    if not os.path.exists(db_path):
        st.info("No FAQs generated yet. They will appear here after some chats are completed.")
        return

    try:
        faq_db = FAQDatabase(db_path=db_path)
        top_faqs = faq_db.get_top_faqs(limit=10)
        
        if not top_faqs:
            st.info("No FAQs generated yet. They will appear here after some chats are completed.")
        else:
            for faq in top_faqs:
                with st.expander(f"Q: {faq['question']}"):
                    st.markdown(f"**A:** {faq['answer']}")
                    st.caption(f"Category: {faq.get('category', 'General')}")
    except Exception as e:
        st.error(f"Could not load FAQs: {e}")


def user_type_selection():
    """Display user type selection interface"""
    st.title("⚖️ Legal Assistant")
    
    st.markdown("""
    ### Welcome to your AI Legal Assistant!
    
    Please select your background to get the most appropriate assistance:
    """)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🎓 Legal Professional", use_container_width=True):
            st.session_state.user_type = "Legal Professional"
            st.session_state.is_professional = True
            st.rerun()
    
    with col2:
        if st.button("📚 Law Student", use_container_width=True):
            st.session_state.user_type = "Law Student"
            st.session_state.is_professional = False
            st.rerun()
    
    with col3:
        if st.button("👤 General Public", use_container_width=True):
            st.session_state.user_type = "General Public"
            st.session_state.is_professional = False
            st.rerun()
    
    # Display FAQs on the main page
    display_faqs()


def display_chat_interface():
    """Display the main chat interface"""
    # Header with user type and reset/end chat options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.title("⚖️ Legal Assistant")
    
    with col2:
        if st.button("Change User Type", use_container_width=True):
            reset_conversation()

    with col3:
        if st.button("End Chat", use_container_width=True, type="primary"):
            trigger_faq_generation()
            reset_conversation()
    
    # Display chat messages
    for message in st.session_state.messages:
        if isinstance(message, HumanMessage):
            with st.chat_message("user"):
                st.write(message.content)
        elif isinstance(message, AIMessage):
            with st.chat_message("assistant"):
                st.write(message.content)
    
    # Chat input
    if prompt := st.chat_input("Ask your legal question..."):
        user_message = HumanMessage(content=prompt)
        st.session_state.messages.append(user_message)
        
        with st.chat_message("user"):
            st.write(prompt)
        
        with st.chat_message("assistant"):
            try:
                graph_input = {
                    "messages": st.session_state.messages.copy(),
                    "is_professional": st.session_state.is_professional
                }

                def stream_generator(input_data):
                    for chunk, metadata in legal_assistant.stream(input_data, stream_mode="messages"):
                        if metadata.get("langgraph_node") == "assistant" and chunk.content:
                            yield chunk.content
                
                full_response = st.write_stream(stream_generator(graph_input))
                assistant_message = AIMessage(content=full_response)
                st.session_state.messages.append(assistant_message)
                
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