import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from src.graph import legal_assistant
from src.vector_store import VectorStoreManager
from config.database import FAQDatabase
from config.settings import settings
import subprocess
import json
import os
import uuid
import sys
from collections import defaultdict

# Page configuration
st.set_page_config(
    page_title="Legal Assistant",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Managers once using Streamlit's cache
@st.cache_resource
def get_vector_store_manager():
    return VectorStoreManager()

@st.cache_resource
def get_faq_database():
    return FAQDatabase(db_path=settings.DATABASE_PATH)

vector_store_manager = get_vector_store_manager()
faq_db = get_faq_database()

# --- MODIFIED ---
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
    if "viewing_faqs" not in st.session_state:
        st.session_state.viewing_faqs = False
    # Add a dedicated state for sidebar questions
    if "related_questions" not in st.session_state:
        st.session_state.related_questions = []

def trigger_content_generation():
    """Saves conversation and triggers the unified background content generation script."""
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
        
    script_path = "generate_content_task.py"
    command = [sys.executable, script_path, file_path]
    
    try:
        subprocess.Popen(command)
        st.toast("Thanks for your chat! We'll use it to improve future suggestions and FAQs.", icon="✅")
    except Exception as e:
        st.error(f"Failed to start background task: {e}")

# --- MODIFIED ---
def reset_conversation():
    st.session_state.messages = []
    st.session_state.user_type = None
    st.session_state.is_professional = None
    st.session_state.prompt_from_button = None
    # Clear the related questions on reset
    st.session_state.related_questions = []
    st.rerun()

def end_chat_and_reset():
    trigger_content_generation()
    reset_conversation()

def display_faq_page():
    st.title("💡 Frequently Asked Questions")
    if st.button("⬅ Back to Home", type="primary"):
        st.session_state.viewing_faqs = False
        st.rerun()
    
    st.markdown("---")
    all_faqs = faq_db.get_all_faqs()
    if not all_faqs:
        st.info("No FAQs have been generated yet. Complete a few chats and they will appear here.")
        return

    faqs_by_category = defaultdict(list)
    for faq in all_faqs:
        faqs_by_category[faq['category']].append(faq)

    for category, faqs in faqs_by_category.items():
        st.subheader(category)
        for faq in faqs:
            with st.expander(f"Q: {faq['question']}"):
                st.markdown(f"**A:** {faq['answer']}")
        st.markdown("---")

def user_type_selection():
    st.markdown("<h1 style='text-align: center;'>⚖️ Legal Assistant</h1>", unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("### Welcome to your AI Legal Assistant!")
    st.markdown("Please select your background to get the most appropriate assistance:")
    st.markdown("")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div style="text-align: center; padding: 20px; border: 2px solid #1f77b4; border-radius: 10px; margin: 10px 0;"><h3>🎓 Legal Professional</h3><p style="font-size: 14px; color: #666;">For lawyers, paralegals, and legal practitioners seeking detailed legal analysis, case law references, and professional-level insights.</p></div>', unsafe_allow_html=True)
        if st.button("Select Legal Professional", key="legal_prof", use_container_width=True):
            st.session_state.user_type, st.session_state.is_professional = "Legal Professional", True
            st.rerun()
    with col2:
        st.markdown('<div style="text-align: center; padding: 20px; border: 2px solid #ff7f0e; border-radius: 10px; margin: 10px 0;"><h3>📚 Law Student</h3><p style="font-size: 14px; color: #666;">Perfect for law students studying legal concepts, preparing for exams, or working on assignments and research projects.</p></div>', unsafe_allow_html=True)
        if st.button("Select Law Student", key="law_student", use_container_width=True):
            st.session_state.user_type, st.session_state.is_professional = "Law Student", False
            st.rerun()
    with col3:
        st.markdown('<div style="text-align: center; padding: 20px; border: 2px solid #2ca02c; border-radius: 10px; margin: 10px 0;"><h3>👤 General Public</h3><p style="font-size: 14px; color: #666;">For individuals seeking basic legal information, understanding rights, or getting guidance on common legal questions.</p></div>', unsafe_allow_html=True)
        if st.button("Select General Public", key="general_public", use_container_width=True):
            st.session_state.user_type, st.session_state.is_professional = "General Public", False
            st.rerun()
    
    st.markdown("---")
    if st.button("📖 Read Frequently Asked Questions", use_container_width=True):
        st.session_state.viewing_faqs = True
        st.rerun()

def handle_button_click(question: str):
    st.session_state.prompt_from_button = question

# --- MODIFIED ---
def display_chat_interface():
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.title("⚖️ Legal Assistant")
    if col2.button("🔄 Change User Type", use_container_width=True):
        reset_conversation()
    if col3.button("🔚 End Chat", use_container_width=True, help="End this chat and help improve the assistant"):
        end_chat_and_reset()

    # Display chat messages (without related questions)
    for message in st.session_state.messages:
        with st.chat_message("user" if isinstance(message, HumanMessage) else "assistant"):
            st.write(message.content)
            # The logic for displaying questions here has been REMOVED.
    
    prompt = st.session_state.pop('prompt_from_button', None) or st.chat_input("Ask your legal question...")

    if prompt:
        st.session_state.messages.append(HumanMessage(content=prompt))
        st.rerun()
    
    if st.session_state.messages and isinstance(st.session_state.messages[-1], HumanMessage):
        last_user_message = st.session_state.messages[-1]
        with st.chat_message("assistant"):
            try:
                graph_input = {"messages": st.session_state.messages, "is_professional": st.session_state.is_professional}
                
                def stream_generator(input_data):
                    for chunk, metadata in legal_assistant.stream(input_data, stream_mode="messages"):
                        if metadata.get("langgraph_node") == "assistant" and chunk.content:
                            yield chunk.content
                
                full_response = st.write_stream(stream_generator(graph_input))
                
                # Get related questions and store them in the dedicated session state
                st.session_state.related_questions = vector_store_manager.get_similar_faq_questions(last_user_message.content, k=3)
                
                # The AIMessage no longer needs additional_kwargs for this
                assistant_message = AIMessage(content=full_response)
                st.session_state.messages.append(assistant_message)
                st.rerun()

            except Exception as e:
                st.error(f"An error occurred: {str(e)}")

# --- MODIFIED ---
def add_sidebar():
    with st.sidebar:
        st.header("ℹ️ Information")
        st.markdown(f"**User Type:** {st.session_state.user_type}\n\n**Messages:** {len(st.session_state.messages)}")
        st.markdown("---")
        
        # Display related questions here
        if st.session_state.related_questions:
            st.subheader("Related Questions")
            for i, q in enumerate(st.session_state.related_questions):
                if st.button(q, key=f"sidebar_q_{i}", on_click=handle_button_click, args=(q,), use_container_width=True):
                    pass
            st.markdown("---")

        st.markdown("**Disclaimer:** This is not legal advice. Consult a qualified attorney for specific legal matters.")
        st.markdown("---")
        if st.button("🗑️ Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.related_questions = [] # Also clear questions
            st.rerun()

def main():
    """Main application router."""
    initialize_session_state()

    if st.session_state.viewing_faqs:
        display_faq_page()
    elif st.session_state.user_type is None:
        user_type_selection()
    else:
        add_sidebar()
        display_chat_interface()

if __name__ == "__main__":
    main()