"""
Streamlit UI for bAIt-Chat
Main chat interface with voice input support
"""

import streamlit as st
import requests
import json
from datetime import datetime
import asyncio
import base64
from typing import Dict, Any, List
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components import (
    DeviceListComponent,
    PlanViewerComponent,
    QueueStatusComponent,
    ScanResultComponent,
    VoiceInputComponent
)

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
ENABLE_VOICE = os.getenv("ENABLE_VOICE", "false").lower() == "true"

# Page configuration
st.set_page_config(
    page_title="bAIt-Chat - Beamline Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .stApp {
        max-width: 1400px;
        margin: 0 auto;
    }
    .chat-message {
        padding: 1rem;
        margin-bottom: 1rem;
        border-radius: 0.5rem;
    }
    .user-message {
        background-color: #e3f2fd;
    }
    .assistant-message {
        background-color: #f5f5f5;
    }
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 5px;
    }
    .status-online {
        background-color: #4caf50;
    }
    .status-offline {
        background-color: #f44336;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_status" not in st.session_state:
    st.session_state.api_status = False
if "current_scan" not in st.session_state:
    st.session_state.current_scan = None
if "queue_status" not in st.session_state:
    st.session_state.queue_status = None


def check_api_status():
    """Check if the backend API is available"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=2)
        if response.status_code == 200:
            return True
    except:
        pass
    return False


def send_message(message: str) -> Dict[str, Any]:
    """Send message to the backend API"""
    try:
        # For Phase 1, we'll use the specific endpoints
        # In Phase 1.5, this would go through the agent
        
        message_lower = message.lower()
        
        # Route to appropriate endpoint based on message content
        if "device" in message_lower or "motor" in message_lower:
            response = requests.get(f"{API_BASE_URL}/devices")
            if response.status_code == 200:
                devices = response.json()
                return {
                    "type": "devices",
                    "data": devices,
                    "message": f"Found {len(devices)} devices"
                }
        
        elif "plan" in message_lower or "scan" in message_lower and "last" not in message_lower:
            response = requests.get(f"{API_BASE_URL}/plans")
            if response.status_code == 200:
                plans = response.json()
                return {
                    "type": "plans",
                    "data": plans,
                    "message": f"Found {len(plans)} available plans"
                }
        
        elif "last" in message_lower and "scan" in message_lower:
            response = requests.get(f"{API_BASE_URL}/last_scan")
            if response.status_code == 200:
                scan = response.json()
                return {
                    "type": "scan",
                    "data": scan,
                    "message": "Retrieved last scan information"
                }
        
        elif "explain" in message_lower:
            # Extract plan name (simplified)
            plan_name = "scan"  # Default
            response = requests.post(
                f"{API_BASE_URL}/explain",
                json={"plan_name": plan_name}
            )
            if response.status_code == 200:
                explanation = response.json()
                return {
                    "type": "explanation",
                    "data": explanation,
                    "message": explanation["explanation"]
                }
        
        else:
            # General search
            response = requests.get(
                f"{API_BASE_URL}/search",
                params={"query": message}
            )
            if response.status_code == 200:
                results = response.json()
                return {
                    "type": "search",
                    "data": results,
                    "message": f"Found {len(results['results'])} relevant results"
                }
        
    except Exception as e:
        return {
            "type": "error",
            "message": f"Error: {str(e)}"
        }
    
    return {
        "type": "info",
        "message": "I can help you with devices, plans, scans, and explanations. Try asking about available motors or scan plans."
    }


def main():
    """Main Streamlit application"""
    
    # Header
    col1, col2 = st.columns([6, 1])
    with col1:
        st.title("🔬 bAIt-Chat - Beamline AI Assistant")
        st.caption("Your intelligent assistant for beamline control and experiment management")
    
    with col2:
        # API Status indicator
        api_status = check_api_status()
        st.session_state.api_status = api_status
        
        if api_status:
            st.markdown(
                '<span class="status-indicator status-online"></span>API Online',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<span class="status-indicator status-offline"></span>API Offline',
                unsafe_allow_html=True
            )
    
    # Sidebar
    with st.sidebar:
        st.header("Quick Actions")
        
        # Quick action buttons
        if st.button("📋 List Devices", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "Show me available devices"
            })
            st.rerun()
        
        if st.button("📊 List Plans", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "What scan plans are available?"
            })
            st.rerun()
        
        if st.button("🔍 Last Scan", use_container_width=True):
            st.session_state.messages.append({
                "role": "user",
                "content": "What was the last scan?"
            })
            st.rerun()
        
        st.divider()
        
        # Queue Status (Phase 1.5 placeholder)
        st.header("Queue Status")
        queue_component = QueueStatusComponent()
        queue_component.render()
        
        st.divider()
        
        # Settings
        st.header("Settings")
        
        # Voice input toggle
        if ENABLE_VOICE:
            voice_enabled = st.checkbox("Enable Voice Input", value=False)
        
        # Theme selection
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "Auto"],
            index=0
        )
        
        # Advanced settings
        with st.expander("Advanced Settings"):
            st.number_input(
                "Max Results",
                min_value=1,
                max_value=20,
                value=5,
                key="max_results"
            )
            
            st.checkbox("Show Technical Details", key="show_technical")
            st.checkbox("Enable Notifications", key="enable_notifications")
    
    # Main chat interface
    chat_container = st.container()
    
    # Display chat messages
    with chat_container:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                if message["role"] == "user":
                    st.write(message["content"])
                else:
                    # Assistant message
                    st.write(message.get("content", ""))
                    
                    # Display specialized content based on response type
                    if "data" in message:
                        data = message["data"]
                        msg_type = message.get("type", "")
                        
                        if msg_type == "devices":
                            device_component = DeviceListComponent(data)
                            device_component.render()
                        
                        elif msg_type == "plans":
                            plan_component = PlanViewerComponent(data)
                            plan_component.render()
                        
                        elif msg_type == "scan":
                            scan_component = ScanResultComponent(data)
                            scan_component.render()
                        
                        elif msg_type == "search" and "results" in data:
                            st.subheader("Search Results")
                            for result in data["results"][:5]:
                                with st.expander(f"📄 {result.get('metadata', {}).get('source', 'Unknown')}"):
                                    st.write(result.get("content", ""))
                                    st.caption(f"Relevance: {result.get('score', 0):.2%}")
    
    # Chat input
    col1, col2 = st.columns([10, 1])
    
    with col1:
        user_input = st.chat_input(
            "Ask me about devices, plans, or scans...",
            key="chat_input"
        )
    
    with col2:
        # Voice input button (if enabled)
        if ENABLE_VOICE and "voice_enabled" in locals() and voice_enabled:
            voice_component = VoiceInputComponent()
            voice_text = voice_component.render()
            if voice_text:
                user_input = voice_text
    
    # Process user input
    if user_input:
        # Add user message to chat
        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })
        
        # Get response from API
        with st.spinner("Thinking..."):
            response = send_message(user_input)
        
        # Add assistant response to chat
        assistant_message = {
            "role": "assistant",
            "content": response.get("message", ""),
            "type": response.get("type"),
            "data": response.get("data")
        }
        st.session_state.messages.append(assistant_message)
        
        # Rerun to update display
        st.rerun()
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🔬 bAIt-Chat v0.1.0")
    
    with col2:
        st.caption("Phase 1: Informational + RAG")
    
    with col3:
        st.caption(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# Example prompts for new users
def show_example_prompts():
    """Display example prompts for new users"""
    st.info("**Try asking:**")
    examples = [
        "What motors can I use?",
        "Show me available scan plans",
        "What was the last scan?",
        "Explain the scan plan",
        "Search for Pilatus detector information"
    ]
    
    cols = st.columns(len(examples))
    for i, example in enumerate(examples):
        with cols[i]:
            if st.button(example, key=f"example_{i}", use_container_width=True):
                st.session_state.messages.append({
                    "role": "user",
                    "content": example
                })
                st.rerun()


if __name__ == "__main__":
    # Show example prompts if no messages
    if not st.session_state.messages:
        show_example_prompts()
    
    # Run main application
    main()