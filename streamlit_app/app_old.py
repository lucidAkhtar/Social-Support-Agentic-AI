"""
Streamlit UI for Social Support System.
Multi-page application with document upload, processing, and chatbot.
"""

import streamlit as st
import requests
import time
from pathlib import Path
from typing import Optional, Dict, Any
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="UAE Social Support System",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        padding-bottom: 2rem;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-pending {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
    }
    .status-processing {
        background-color: #d1ecf1;
        border: 2px solid #17a2b8;
    }
    .status-completed {
        background-color: #d4edda;
        border: 2px solid #28a745;
    }
    .status-error {
        background-color: #f8d7da;
        border: 2px solid #dc3545;
    }
    .metric-card {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
    }
    .chat-message-user {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
    }
    .chat-message-assistant {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'application_id' not in st.session_state:
    st.session_state.application_id = None
if 'applicant_name' not in st.session_state:
    st.session_state.applicant_name = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'current_stage' not in st.session_state:
    st.session_state.current_stage = "not_started"


def create_application(name: str) -> Optional[str]:
    """Create a new application."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/create",
            data={"applicant_name": name}
        )
        response.raise_for_status()
        data = response.json()
        return data['application_id']
    except Exception as e:
        st.error(f"Error creating application: {e}")
        return None


def upload_documents(application_id: str, files) -> bool:
    """Upload documents to API."""
    try:
        files_data = [("documents", (file.name, file, file.type)) for file in files]
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/upload",
            files=files_data
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error uploading documents: {e}")
        return False


def process_application(application_id: str) -> bool:
    """Process application through all agents."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/process"
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"Error processing application: {e}")
        return False


def get_application_status(application_id: str) -> Optional[Dict]:
    """Get application status."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/applications/{application_id}/status"
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting status: {e}")
        return None


def get_application_results(application_id: str) -> Optional[Dict]:
    """Get complete application results."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/applications/{application_id}/results"
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error getting results: {e}")
        return None


def chat_with_agent(application_id: str, query: str, query_type: str = "explanation") -> Optional[str]:
    """Send chat query to agent."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/chat",
            json={
                "application_id": application_id,
                "query": query,
                "query_type": query_type
            }
        )
        response.raise_for_status()
        data = response.json()
        return data['response']
    except Exception as e:
        st.error(f"Error in chat: {e}")
        return None


# ========== Main UI ==========

# Header
st.markdown('<div class="main-header">🏛️ UAE Social Support System</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">AI-Powered Eligibility Assessment & Support Recommendation</div>', unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("📋 Application Info")
    
    if st.session_state.application_id:
        st.success(f"**Application ID:** {st.session_state.application_id}")
        st.info(f"**Applicant:** {st.session_state.applicant_name}")
        st.metric("Stage", st.session_state.current_stage.replace("_", " ").title())
        
        if st.button("🔄 Refresh Status"):
            status = get_application_status(st.session_state.application_id)
            if status:
                st.session_state.current_stage = status['current_stage']
                st.rerun()
        
        if st.button("🗑️ New Application"):
            st.session_state.application_id = None
            st.session_state.applicant_name = None
            st.session_state.processing_complete = False
            st.session_state.chat_history = []
            st.session_state.current_stage = "not_started"
            st.rerun()
    else:
        st.warning("No active application")
    
    st.divider()
    
    # System stats
    st.header("📊 System Stats")
    try:
        response = requests.get(f"{API_BASE_URL}/api/statistics")
        if response.status_code == 200:
            stats = response.json()
            st.metric("Total Applications", stats.get('total_applications', 0))
            st.metric("Active Sessions", stats.get('active_applications', 0))
    except:
        pass


# Main content area
tab1, tab2, tab3, tab4 = st.tabs(["📝 New Application", "📄 Documents", "✅ Results", "💬 Chatbot"])

# Tab 1: New Application
with tab1:
    st.header("Start New Application")
    
    if not st.session_state.application_id:
        st.info("👋 Welcome! Please enter your details to begin your social support application.")
        
        with st.form("application_form"):
            applicant_name = st.text_input(
                "Full Name *",
                placeholder="Enter your full name as it appears on your Emirates ID"
            )
            
            st.markdown("---")
            st.caption("After creating your application, you'll be able to upload your documents.")
            
            submitted = st.form_submit_button("Create Application", type="primary", use_container_width=True)
            
            if submitted:
                if not applicant_name or len(applicant_name.strip()) < 2:
                    st.error("Please enter a valid name.")
                else:
                    with st.spinner("Creating your application..."):
                        app_id = create_application(applicant_name.strip())
                        if app_id:
                            st.session_state.application_id = app_id
                            st.session_state.applicant_name = applicant_name.strip()
                            st.success(f"✅ Application created! ID: {app_id}")
                            time.sleep(1)
                            st.rerun()
    else:
        st.success(f"✅ Application already created: {st.session_state.application_id}")
        st.info("👉 Go to the **Documents** tab to upload your documents.")


# Tab 2: Documents Upload
with tab2:
    st.header("Upload Documents")
    
    if not st.session_state.application_id:
        st.warning("⚠️ Please create an application first in the **New Application** tab.")
    else:
        st.info(f"📋 Application ID: **{st.session_state.application_id}**")
        
        st.markdown("""
        ### Required Documents:
        Please upload the following documents:
        1. 🆔 **Emirates ID** (front and back)
        2. 📄 **Resume/CV** (PDF or image)
        3. 🏦 **Bank Statement** (last 6 months)
        4. 📊 **Assets & Liabilities** (Excel or document)
        5. 💡 **Utility Bill** (recent bill showing address)
        """)
        
        uploaded_files = st.file_uploader(
            "Choose files to upload",
            type=['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls', 'csv', 'txt'],
            accept_multiple_files=True,
            help="You can upload multiple files at once"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            if uploaded_files and st.button("📤 Upload Documents", type="primary", use_container_width=True):
                with st.spinner(f"Uploading {len(uploaded_files)} file(s)..."):
                    success = upload_documents(st.session_state.application_id, uploaded_files)
                    if success:
                        st.success(f"✅ Successfully uploaded {len(uploaded_files)} document(s)!")
        
        with col2:
            if st.button("🚀 Process Application", type="primary", use_container_width=True):
                with st.spinner("Processing your application through all agents..."):
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Start processing
                    success = process_application(st.session_state.application_id)
                    
                    if success:
                        # Simulate progress updates
                        stages = ["Extracting", "Validating", "Eligibility Check", "Generating Recommendation", "Completed"]
                        for i, stage in enumerate(stages):
                            progress = (i + 1) / len(stages)
                            progress_bar.progress(progress)
                            status_text.text(f"Status: {stage}...")
                            time.sleep(0.5)
                        
                        st.session_state.processing_complete = True
                        st.session_state.current_stage = "completed"
                        st.success("✅ Application processing completed!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()


# Tab 3: Results
with tab3:
    st.header("Application Results")
    
    if not st.session_state.application_id:
        st.warning("⚠️ No application to display results for.")
    elif not st.session_state.processing_complete:
        st.info("⏳ Application is being processed. Please wait...")
        
        # Auto-refresh status
        if st.button("🔄 Check Status"):
            status = get_application_status(st.session_state.application_id)
            if status and status['current_stage'] == 'completed':
                st.session_state.processing_complete = True
                st.session_state.current_stage = 'completed'
                st.rerun()
    else:
        results = get_application_results(st.session_state.application_id)
        
        if results:
            # Decision Summary
            if results.get('recommendation'):
                rec = results['recommendation']
                decision = rec['decision']
                
                if decision == 'APPROVED':
                    st.success("🎉 **APPROVED** - Congratulations!")
                    st.metric("Support Amount", f"{rec['support_amount']:.2f} AED")
                elif decision == 'SOFT_DECLINED':
                    st.warning("⚠️ **SOFT DECLINED** - Eligibility programs available")
                else:
                    st.error("❌ **DECLINED**")
                
                st.markdown(f"**Reasoning:** {rec['reasoning']}")
            
            # Eligibility Score
            st.divider()
            st.subheader("📊 Eligibility Analysis")
            
            if results.get('eligibility'):
                elig = results['eligibility']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Overall Score", f"{elig['eligibility_score']:.2f}")
                with col2:
                    st.metric("Eligible", "Yes" if elig['is_eligible'] else "No")
                
                st.markdown("**Reasoning:**")
                for reason in elig['reasoning']:
                    st.markdown(f"- {reason}")
            
            # Validation Report
            st.divider()
            st.subheader("✅ Validation Report")
            
            if results.get('validation'):
                val = results['validation']
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Completeness", f"{val['completeness_score']:.2%}")
                with col2:
                    st.metric("Confidence", f"{val['confidence_score']:.2%}")
                
                if val['is_valid']:
                    st.success("✅ All documents validated successfully")
                else:
                    st.warning("⚠️ Some validation issues found")
                    for issue in val['issues']:
                        st.markdown(f"- **{issue['field']}**: {issue['message']}")
            
            # Extracted Data
            st.divider()
            st.subheader("📋 Extracted Data")
            
            if results.get('extracted_data'):
                data = results['extracted_data']
                
                if data.get('applicant_info'):
                    with st.expander("🆔 Applicant Information"):
                        st.json(data['applicant_info'])
                
                if data.get('employment_data'):
                    with st.expander("📄 Employment Data"):
                        st.json(data['employment_data'])
                
                if data.get('income_data'):
                    with st.expander("🏦 Income Data"):
                        st.json(data['income_data'])
                
                if data.get('assets_liabilities'):
                    with st.expander("💰 Assets & Liabilities"):
                        st.json(data['assets_liabilities'])
            
            # Enablement Programs
            if results.get('recommendation') and results['recommendation'].get('programs'):
                st.divider()
                st.subheader("🎓 Recommended Programs")
                
                programs = results['recommendation']['programs']
                if programs:
                    for i, program in enumerate(programs):
                        with st.expander(f"📌 Program {i+1}"):
                            st.json(program)


# Tab 4: Chatbot
with tab4:
    st.header("💬 AI Assistant")
    
    if not st.session_state.application_id:
        st.warning("⚠️ Please create an application first.")
    elif not st.session_state.processing_complete:
        st.info("🔒 The chatbot will be available after your application is validated.")
        st.markdown("""
        **The chatbot can help you with:**
        - 💡 Understanding your eligibility decision
        - 🔮 Simulating what-if scenarios
        - 🔍 Reviewing data inconsistencies
        - 📊 Explaining scoring details
        
        Please complete document upload and processing first.
        """)
    else:
        st.success("✅ Chatbot is now active! Ask me anything about your application.")
        
        # Chat history
        chat_container = st.container()
        
        with chat_container:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f'<div class="chat-message-user">👤 **You:** {message["content"]}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="chat-message-assistant">🤖 **Assistant:** {message["content"]}</div>', unsafe_allow_html=True)
        
        # Quick action buttons
        st.markdown("### Quick Questions")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💡 Why this decision?", use_container_width=True):
                query = "Why was I approved/declined?"
                response = chat_with_agent(st.session_state.application_id, query, "explanation")
                if response:
                    st.session_state.chat_history.append({"role": "user", "content": query})
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
        
        with col2:
            if st.button("🔮 Simulate changes", use_container_width=True):
                query = "What if my income increases to 7000 AED?"
                response = chat_with_agent(st.session_state.application_id, query, "simulation")
                if response:
                    st.session_state.chat_history.append({"role": "user", "content": query})
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
        
        with col3:
            if st.button("🔍 Check inconsistencies", use_container_width=True):
                query = "Show me any data inconsistencies"
                response = chat_with_agent(st.session_state.application_id, query, "audit")
                if response:
                    st.session_state.chat_history.append({"role": "user", "content": query})
                    st.session_state.chat_history.append({"role": "assistant", "content": response})
                    st.rerun()
        
        # Chat input
        st.divider()
        with st.form("chat_form", clear_on_submit=True):
            user_input = st.text_input(
                "Ask a question:",
                placeholder="Type your question here...",
                label_visibility="collapsed"
            )
            
            col1, col2 = st.columns([6, 1])
            with col2:
                send_button = st.form_submit_button("Send", type="primary", use_container_width=True)
            
            if send_button and user_input:
                with st.spinner("Thinking..."):
                    response = chat_with_agent(st.session_state.application_id, user_input)
                    if response:
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.rerun()


# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>🏛️ UAE Social Support System | Powered by Multi-Agent AI</p>
    <p><small>Built with FastAPI + Streamlit | SQLite + ChromaDB + Neo4j</small></p>
</div>
""", unsafe_allow_html=True)
