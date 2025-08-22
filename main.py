import streamlit as st
import time
from typing import Any
from datetime import datetime
from local_models import LocalModelFallback
import os
import json

# Import custom modules
from auth import (
    init_db as init_auth_db,
    register_user,
    authenticate_user,
    create_session_token,
    verify_session_token,
    get_user_info,
    logout_user,
)
from database import ChatDatabase
from agentic_engine import NeuroSyncAgent
from utils import (
    apply_theme,
    format_message,
    generate_conversation_stats,
    create_stats_visualization,
    export_conversation,
    format_roadmap_response,
)

# ----------------- Page configuration -----------------
st.set_page_config(
    page_title="NeuroSync - Intelligent AI Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------- Helpers -----------------
def load_css():
    """Load custom CSS if present"""
    css_path = "style.css"
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    
    # Load hover effects
    js_path = "hover.js"
    if os.path.exists(js_path):
        with open(js_path) as f:
            st.components.v1.html(f"<script>{f.read()}</script>", height=0)
    
    # Load Mermaid.js for flowcharts
    st.markdown("""
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.6.1/dist/mermaid.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            if (typeof mermaid !== 'undefined') {
                mermaid.initialize({ 
                    startOnLoad: true,
                    theme: 'default',
                    securityLevel: 'loose'
                });
                mermaid.init(undefined, '.mermaid');
            }
        });
        
        function copyCode(codeId) {
            const codeElement = document.getElementById(codeId);
            const textArea = document.createElement('textarea');
            textArea.value = codeElement.textContent;
            document.body.appendChild(textArea);
            textArea.select();
            document.execCommand('copy');
            document.body.removeChild(textArea);
            
            // Show copied notification
            const notification = document.createElement('div');
            notification.style.position = 'fixed';
            notification.style.top = '20px';
            notification.style.right = '20px';
            notification.style.backgroundColor = '#8A2BE2';
            notification.style.color = 'white';
            notification.style.padding = '10px 15px';
            notification.style.borderRadius = '5px';
            notification.style.zIndex = '10000';
            notification.textContent = 'Code copied to clipboard!';
            document.body.appendChild(notification);
            
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 2000);
        }
        
        function runCode(codeId) {
            // This would need to be implemented based on your specific needs
            alert('Run code functionality would be implemented here. Code ID: ' + codeId);
        }
    </script>
    """, unsafe_allow_html=True)

def init_session_state():
    """Ensure required session state keys exist"""
    defaults = {
        "authenticated": False,
        "user_id": None,
        "username": None,
        "session_token": None,
        "current_conversation": None,
        "chat_engine": None,
        "messages": [],
        "theme": "dark",
        "chat_summary": None,
        "user_prefs": {"theme": "dark", "auto_summarize": False},
        "show_roadmap": False,
        "roadmap_content": "",
        "api_error": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def process_message(message: str):
    """Process a user message and generate AI response"""
    db = ChatDatabase()

    # Create new conversation if none exists
    if st.session_state.current_conversation is None:
        conv_title = message[:30] + "..." if len(message) > 30 else message
        st.session_state.current_conversation = db.create_conversation(
            st.session_state.user_id, conv_title
        )

    # Add user message
    db.add_message(st.session_state.current_conversation, "user", message)
    st.session_state.messages.append(
        ("user", message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None)
    )

    # Check if this is a roadmap request
    roadmap_triggers = ["roadmap", "learning path", "step by step", "plan", "timeline"]
    is_roadmap_request = any(trigger in message.lower() for trigger in roadmap_triggers)
    
    # Generate AI response
    with st.spinner("NeuroSync is thinking..."):
        try:
            ai_response = st.session_state.chat_engine.generate_response(message)
            st.session_state.api_error = False
        except Exception as e:
            # Try fallback to local model
            if "local_fallback" not in st.session_state:
                st.session_state.local_fallback = LocalModelFallback()
            
            ai_response = st.session_state.local_fallback.generate_response(
                message, 
                st.session_state.messages
            )
            st.session_state.api_error = True
    
    # Check if the response contains roadmap content
    if is_roadmap_request or "phase" in ai_response.lower() or "step" in ai_response.lower():
        st.session_state.show_roadmap = True
        st.session_state.roadmap_content = ai_response
    else:
        st.session_state.show_roadmap = False

    # Add AI response
    db.add_message(st.session_state.current_conversation, "assistant", ai_response)
    st.session_state.messages.append(
        ("assistant", ai_response, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), None)
    )

    # Auto-summarize if enabled and conversation is long
    if st.session_state.user_prefs.get("auto_summarize", False) and len(st.session_state.messages) >= 10:
        summarize_chat()

    st.rerun()




def summarize_chat():
    """Generate a short summary of current conversation"""
    if not st.session_state.messages:
        st.warning("No messages to summarize yet.")
        return

    conv_text = "\n".join(
        f"{role.upper()}: {content}" for role, content, _, _ in st.session_state.messages
    )
    with st.spinner("Summarizing conversation..."):
        try:
            summary = st.session_state.chat_engine.generate_response(
                f"Summarize this conversation in 3-4 bullet points:\n{conv_text}"
            )
            st.session_state.chat_summary = summary
        except Exception as e:
            st.error(f"Failed to generate summary: {str(e)}")

def update_user_preferences():
    """Update user preferences in database"""
    db = ChatDatabase()
    db.update_user_preferences(
        st.session_state.user_id,
        st.session_state.user_prefs["theme"],
        st.session_state.user_prefs["auto_summarize"]
    )

# ----------------- Auth Page -----------------
def auth_page():
    st.markdown(
        """
        <div class="app-header">
            <h1 class="app-title">NeuroSync</h1>
            <p class="app-subtitle">Intelligent Conversations Powered by Agentic AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab1, tab2 = st.tabs(["Login", "Register"])

    # ---- Login ----
    with tab1:
        with st.form("login_form"):
            st.subheader("Welcome Back!")
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            login_btn = st.form_submit_button("Login", use_container_width=True, type="primary")

            if login_btn:
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    success, user_id, message = authenticate_user(username, password)
                    if success:
                        session_token = create_session_token(user_id)
                        # Get user preferences
                        db = ChatDatabase()
                        prefs = db.get_user_preferences(user_id)
                        
                        # Initialize chat engine
                        try:
                            chat_engine = NeuroSyncAgent()
                            st.session_state.update(
                                {
                                    "authenticated": True,
                                    "user_id": user_id,
                                    "username": username,
                                    "session_token": session_token,
                                    "user_prefs": prefs,
                                    "chat_engine": chat_engine,
                                    "api_error": False,
                                }
                            )
                            st.success("Login successful! Redirecting...")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to initialize AI engine: {str(e)}. Please check your GOOGLE_API_KEY configuration.")
                    else:
                        st.error(message)

    # ---- Register ----
    with tab2:
        with st.form("register_form"):
            st.subheader("Create an Account")
            new_username = st.text_input("Choose a username")
            new_email = st.text_input("Email address")
            new_password = st.text_input("Create a password", type="password")
            confirm_password = st.text_input("Confirm password", type="password")
            full_name = st.text_input("Full name (optional)")
            register_btn = st.form_submit_button("Register", use_container_width=True, type="primary")

            if register_btn:
                if not new_username or not new_email or not new_password:
                    st.error("Please fill in all required fields")
                elif new_password != confirm_password:
                    st.error("Passwords don't match")
                else:
                    success, message = register_user(
                        new_username, new_password, new_email, full_name
                    )
                    if success:
                        st.success(message + " You can now login.")
                    else:
                        st.error(message)

# ----------------- Main Chat Page -----------------
def main_chat_page():
    db = ChatDatabase()
    
    # Sidebar
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-header">
                <h3 class="sidebar-title">NeuroSync</h3>
                <p class="sidebar-subtitle">Intelligent AI Assistant</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.write(f"Welcome, **{st.session_state.username}**!")
        
        # Theme selector
        theme = st.selectbox(
            "Theme",
            ["dark", "light"],
            index=0 if st.session_state.user_prefs["theme"] == "dark" else 1,
            key="theme_selector",
        )
        
        if theme != st.session_state.user_prefs["theme"]:
            st.session_state.user_prefs["theme"] = theme
            update_user_preferences()
            st.rerun()
        
        # Auto-summarize toggle
        auto_summarize = st.toggle(
            "Auto-summarize long chats",
            value=st.session_state.user_prefs["auto_summarize"],
            key="auto_summarize_toggle",
        )
        
        if auto_summarize != st.session_state.user_prefs["auto_summarize"]:
            st.session_state.user_prefs["auto_summarize"] = auto_summarize
            update_user_preferences()
        
        st.divider()
        
        # Conversation history
        st.subheader("Conversations")
        conversations = db.get_user_conversations(st.session_state.user_id)
        
        if conversations:
            for conv_id, title, created, updated in conversations:
                col1, col2 = st.columns([4, 1])
                with col1:
                    if st.button(
                        f"{title}",
                        key=f"conv_{conv_id}",
                        use_container_width=True,
                    ):
                        load_conversation(conv_id)
                with col2:
                    if st.button(
                        "🗑️", 
                        key=f"delete_{conv_id}",
                        help="Delete this conversation"
                    ):
                        db.delete_conversation(conv_id)
                        st.rerun()
        
        # New conversation button
        if st.button("+ New Conversation", use_container_width=True, type="primary"):
            new_conversation()
        
        st.divider()
        
        # Quick actions
        st.subheader("Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Stats", use_container_width=True):
                st.session_state.show_stats = True
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                clear_chat()
        
        if st.button("📤 Export Chat", use_container_width=True):
            export_chat()
        
        if st.button("🔍 Search Chats", use_container_width=True):
            st.session_state.show_search = True
        
        st.divider()
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            logout_user(st.session_state.session_token)
            st.session_state.clear()
            st.rerun()
    
    # Main chat area
    st.markdown(
        """
        <div class="app-header">
            <h1 class="app-title">NeuroSync</h1>
            <p class="app-subtitle">Intelligent Conversations Powered by Agentic AI</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    
    # Chat container
    chat_container = st.container()
    
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        
        # Display messages
        for role, content, timestamp, metadata in st.session_state.messages:
            if role == "user":
                st.markdown(
                    format_message(content, timestamp, "user"),
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    format_message(content, timestamp, "ai"),
                    unsafe_allow_html=True,
                )
        
        # Show roadmap if requested
        if st.session_state.show_roadmap and st.session_state.roadmap_content:
            st.markdown(
                format_roadmap_response(st.session_state.roadmap_content),
                unsafe_allow_html=True,
            )
        
        # Show stats if requested
        if st.session_state.get("show_stats", False):
            stats = generate_conversation_stats(st.session_state.messages)
            st.plotly_chart(create_stats_visualization(stats), use_container_width=True)
            st.session_state.show_stats = False
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input area
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    user_input = st.chat_input("Message NeuroSync...")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if user_input:
        process_message(user_input)

# ----------------- Helper Functions -----------------
def load_conversation(conversation_id: int):
    """Load a conversation from database"""
    db = ChatDatabase()
    messages = db.get_conversation_messages(conversation_id)
    
    st.session_state.current_conversation = conversation_id
    st.session_state.messages = []
    
    for role, content, timestamp, metadata in messages:
        st.session_state.messages.append((role, content, timestamp, metadata))
    
    st.rerun()

def new_conversation():
    """Start a new conversation"""
    st.session_state.current_conversation = None
    st.session_state.messages = []
    st.session_state.chat_summary = None
    st.session_state.show_roadmap = False
    st.session_state.roadmap_content = ""
    st.rerun()

def clear_chat():
    """Clear current chat"""
    st.session_state.messages = []
    st.session_state.chat_summary = None
    st.session_state.show_roadmap = False
    st.session_state.roadmap_content = ""
    st.rerun()

def export_chat():
    """Export current conversation"""
    if not st.session_state.messages:
        st.warning("No conversation to export")
        return
    
    export_data = export_conversation(st.session_state.messages)
    st.download_button(
        label="Download conversation",
        data=export_data,
        file_name=f"neurosync_chat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        use_container_width=True,
    )

# ----------------- App Initialization -----------------
def main():
    # Initialize databases
    init_auth_db()
    db = ChatDatabase()
    db.init_db()
    
    # Load CSS and initialize session state
    load_css()
    init_session_state()
    apply_theme(st.session_state.user_prefs["theme"])
    
    # Check authentication
    if not st.session_state.authenticated:
        auth_page()
    else:
        main_chat_page()

if __name__ == "__main__":
    main()