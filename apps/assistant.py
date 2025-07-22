import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage, AIMessageChunk
from src.graph import legal_assistant

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

def user_type_selection():
    """Display user type selection interface"""
    st.title("⚖️ Legal Assistant")
    st.markdown("---")
    
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
    
    st.markdown("---")
    st.markdown("""
    **Legal Professional**: Get detailed legal analysis, case law references, and professional-level responses.
    
    **Law Student**: Receive educational explanations with learning-focused content and study materials.
    
    **General Public**: Get simple, easy-to-understand legal information and guidance.
    """)

def display_chat_interface():
    """Display the main chat interface"""
    # Header with user type and reset option
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.title("⚖️ Legal Assistant")
    
    with col2:
        if st.button("🔄 Change User Type", use_container_width=True):
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
        # Add user message to session state
        user_message = HumanMessage(content=prompt)
        st.session_state.messages.append(user_message)
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
        
        # Get assistant response
        with st.chat_message("assistant"):

            try:
                graph_input = {
                    "messages": st.session_state.messages.copy(),
                    "is_professional": st.session_state.is_professional
                }

                # 1. Define a generator function to yield tokens from the LangGraph stream
                def stream_generator(input_data):
                    for chunk, metadata in legal_assistant.stream(input_data, stream_mode="messages"):
                        # We are interested in the content of AIMessageChunk objects
                        if metadata.get("langgraph_node") == "assistant" and chunk.content:
                            yield chunk.content
                
                # 2. Use st.write_stream to render the output in real-time
                #    It will consume the generator and return the full response string at the end.
                full_response = st.write_stream(stream_generator(graph_input))

                # 3. Add the complete assistant message to the session state
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
        
        st.markdown("---")


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