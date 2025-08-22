# utils.py
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime
import streamlit as st
from typing import List, Tuple, Dict, Any
import json
import re
import random

def apply_theme(theme: str):
    """Apply the selected theme"""
    if theme == "dark":
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #0b1020;
                color: #E6E6FA;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            """
            <style>
            .stApp {
                background-color: #F5F5F5;
                color: #4B0082;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

def format_message(content: str, timestamp: str, role: str) -> str:
    """Format a message with HTML styling, including code blocks with explanations"""
    # Check if message contains code blocks with explanations
    if role == "assistant" and ('```' in content or 'def ' in content or 'function ' in content or 'class ' in content):
        # Format the entire content as a code explanation block
        return f"""
        <div class="code-explanation-block">
            <div class="code-content">
                {content.replace('\n', '<br>')}
            </div>
            <div class="message-time">{timestamp}</div>
        </div>
        """
    else:
        if role == "user":
            return f"""
            <div class="user-message">
                <div>{content}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """
        else:
            return f"""
            <div class="ai-message">
                <div>{content}</div>
                <div class="message-time">{timestamp}</div>
            </div>
            """

def format_roadmap_response(content: str) -> str:
    """Format a roadmap response with special styling and flowchart support"""
    # Remove "Your Learning Roadmap" title if present
    content = re.sub(r'(?i)(your learning roadmap|learning roadmap|roadmap)[:\s]*', '', content)
    
    # Check if content contains flowchart syntax
    if "flowchart" in content.lower() or "graph" in content.lower():
        # Extract flowchart code if present
        flowchart_pattern = r'```(?:mermaid)?\s*(flowchart[^`]+)```'
        flowchart_match = re.search(flowchart_pattern, content, re.IGNORECASE)
        
        if flowchart_match:
            flowchart_code = flowchart_match.group(1)
            # Remove the flowchart code from the main content
            content = re.sub(flowchart_pattern, '', content, flags=re.IGNORECASE)
            
            return f"""
            <div class="roadmap-container">
                <div class="roadmap-content">
                    {content.replace('\n', '<br>')}
                </div>
                <div class="flowchart-container">
                    <h4>📊 Process Flowchart</h4>
                    <div class="mermaid">
                        {flowchart_code}
                    </div>
                </div>
            </div>
            """
    
    # Regular roadmap formatting without the title
    return f"""
    <div class="roadmap-container">
        <div class="roadmap-content">
            {content.replace('\n', '<br>')}
        </div>
    </div>
    """

def generate_conversation_stats(messages: List[Tuple]) -> Dict[str, Any]:
    """Generate statistics about the conversation"""
    user_msgs = [msg for msg in messages if msg[0] == "user"]
    ai_msgs = [msg for msg in messages if msg[0] == "assistant"]
    
    total_chars_user = sum(len(msg[1]) for msg in user_msgs)
    total_chars_ai = sum(len(msg[1]) for msg in ai_msgs)
    
    return {
        "total_messages": len(messages),
        "user_messages": len(user_msgs),
        "ai_messages": len(ai_msgs),
        "avg_user_msg_length": total_chars_user / len(user_msgs) if user_msgs else 0,
        "avg_ai_msg_length": total_chars_ai / len(ai_msgs) if ai_msgs else 0,
        "start_time": messages[0][2] if messages else None,
        "end_time": messages[-1][2] if messages else None,
    }

def create_stats_visualization(stats: Dict[str, Any]) -> go.Figure:
    """Create a visualization for conversation statistics"""
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "pie"}, {"type": "bar"}]],
        subplot_titles=("Message Distribution", "Average Message Length")
    )
    
    # Pie chart for message distribution
    fig.add_trace(
        go.Pie(
            labels=["User Messages", "AI Messages"],
            values=[stats["user_messages"], stats["ai_messages"]],
            hole=0.4,
            marker_colors=["#8A2BE2", "#9370DB"]
        ),
        row=1, col=1
    )
    
    # Bar chart for message length
    fig.add_trace(
        go.Bar(
            x=["User", "AI"],
            y=[stats["avg_user_msg_length"], stats["avg_ai_msg_length"]],
            marker_color=["#8A2BE2", "#9370DB"]
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        height=400,
        showlegend=True,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font_color="#E6E6FA"
    )
    
    return fig

def export_conversation(messages: List[Tuple]) -> str:
    """Export conversation to a formatted string"""
    export_lines = ["NeuroSync Conversation Export", "=" * 40, ""]
    
    for role, content, timestamp, _ in messages:
        prefix = "USER: " if role == "user" else "NEUROSYNC: "
        export_lines.append(f"{timestamp} - {prefix}{content}")
        export_lines.append("")
    
    return "\n".join(export_lines)