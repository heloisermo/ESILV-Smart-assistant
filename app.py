"""
Main Streamlit application for ESILV Smart Assistant
Combines the user-facing Assistant tab with the Administration tab for staff
"""
import streamlit as st
import sys
import os

# Configure page
st.set_page_config(
    page_title="ESILV Smart Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add paths for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Back", "app"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "admin_pages"))

# Import agent system for Assistant tab
from agents.orchestrator import OrchestratorAgent
from agents.rag_agent import RAGAgent
from agents.contact_agent import ContactAgent

# Import admin pages
from admin_pages.document_management import render_document_management
from admin_pages.leads_management import render_leads_management


def initialize_session_state():
    """Initialize Streamlit session state variables"""
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = None
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []


def initialize_agents():
    """Initialize the agent system"""
    try:
        orchestrator = OrchestratorAgent()
        
        # Register agents
        try:
            rag_agent = RAGAgent()
            orchestrator.register_agent(rag_agent)
        except Exception as e:
            st.warning(f"⚠️ RAG Agent not available: {str(e)}")
        
        contact_agent = ContactAgent()
        orchestrator.register_agent(contact_agent)
        
        return orchestrator
    
    except Exception as e:
        st.error(f"Error initializing agents: {str(e)}")
        return None


def render_assistant_tab():
    """Render the Assistant tab (user-facing chat interface)"""
    st.header("🤖 ESILV Smart Assistant")
    
    st.write("""
    Welcome to the ESILV Smart Assistant! Ask me any questions about:
    - Programs and courses
    - Admissions and enrollment
    - Student life
    - Contact information
    - And much more!
    """)
    
    st.divider()
    
    # Initialize orchestrator if not already done
    if st.session_state.orchestrator is None:
        with st.spinner("Initializing assistant..."):
            st.session_state.orchestrator = initialize_agents()
    
    orchestrator = st.session_state.orchestrator
    
    if orchestrator is None:
        st.error("❌ Failed to initialize assistant. Please check the logs.")
        return
    
    # Display chat history
    if st.session_state.chat_history:
        st.subheader("Conversation")
        for message in st.session_state.chat_history:
            if message["role"] == "user":
                st.chat_message("user").write(message["content"])
            else:
                st.chat_message("assistant").write(message["content"])
    
    st.divider()
    
    # Chat input
    user_input = st.chat_input(
        "Ask me a question about ESILV...",
        key="user_query"
    )
    
    if user_input:
        # Add user message to history
        st.session_state.chat_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Display user message
        st.chat_message("user").write(user_input)
        
        # Process query through orchestrator
        with st.spinner("Thinking..."):
            try:
                response = orchestrator.route(user_input)
                
                # Extract response text
                if isinstance(response, dict):
                    response_text = response.get("response", "I couldn't process that request.")
                else:
                    response_text = str(response)
                
                # Add assistant response to history
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": response_text
                })
                
                # Display assistant response
                st.chat_message("assistant").write(response_text)
                
            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                st.error(error_msg)
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": error_msg
                })
        
        # Rerun to update the interface
        st.rerun()
    
    # Sidebar info
    with st.sidebar:
        st.header("About")
        st.info("""
        This is the ESILV Smart Assistant, designed to help answer your questions
        about the school, programs, admissions, and more.
        
        **Available agents:**
        - 📚 RAG Agent (Knowledge base search)
        - 📞 Contact Agent (School information)
        """)
        
        st.divider()
        
        if st.button("🗑️ Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()


def render_administration_tab():
    """Render the Administration tab (admin dashboard)"""
    st.header("🔧 Administration Panel")
    
    st.write("""
    Welcome to the ESILV Administration Panel. Here you can:
    - **Manage Documents**: Upload documents and manage the RAG knowledge base
    - **Manage Leads**: View and export contact information collected from users
    """)
    
    st.divider()
    
    # Create sub-tabs for admin sections
    admin_tabs = st.tabs(["📄 Document Management", "📋 Leads Management"])
    
    with admin_tabs[0]:
        render_document_management()
    
    with admin_tabs[1]:
        render_leads_management()
    
    # Admin info sidebar
    with st.sidebar:
        st.header("Admin Info")
        st.info("""
        **Administration Dashboard**
        
        Use this panel to:
        1. Upload and index documents for the RAG system
        2. View collected leads and export data
        
        These tools are for internal use only.
        """)


def main():
    """Main application entry point"""
    initialize_session_state()
    
    # Custom styling
    st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Main navigation tabs
    main_tabs = st.tabs(["🤖 Assistant", "🔧 Administration"])
    
    with main_tabs[0]:
        render_assistant_tab()
    
    with main_tabs[1]:
        render_administration_tab()


if __name__ == "__main__":
    main()
