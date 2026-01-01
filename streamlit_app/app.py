"""
Professional UAE Social Support System UI
Production-grade user experience with clear flow and guidance
"""

import streamlit as st
import requests
import time
from pathlib import Path
from typing import Optional, Dict, Any
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Professional Page Configuration
st.set_page_config(
    page_title="UAE Social Support Portal",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS Styling
st.markdown("""
<style>
    /* Modern color scheme */
    :root {
        --primary: #0066cc;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #3b82f6;
    }
    
    /* Main container */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Professional header */
    .app-header {
        background: linear-gradient(135deg, #0066cc 0%, #004d99 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .app-header h1 {
        margin: 0;
        font-size: 2.5rem;
        font-weight: 700;
    }
    
    .app-header p {
        margin: 0.5rem 0 0 0;
        font-size: 1.1rem;
        opacity: 0.95;
    }
    
    /* Status cards */
    .status-card {
        padding: 1.5rem;
        border-radius: 8px;
        margin: 1rem 0;
        border-left: 4px solid;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    .status-pending {
        background: #fef3c7;
        border-color: #f59e0b;
    }
    
    .status-processing {
        background: #dbeafe;
        border-color: #3b82f6;
    }
    
    .status-success {
        background: #d1fae5;
        border-color: #10b981;
    }
    
    .status-error {
        background: #fee2e2;
        border-color: #ef4444;
    }
    
    /* Progress steps */
    .progress-steps {
        display: flex;
        justify-content: space-between;
        margin: 2rem 0;
        padding: 0;
    }
    
    .step {
        flex: 1;
        text-align: center;
        position: relative;
    }
    
    .step-number {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        background: #e5e7eb;
        color: #6b7280;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        margin-bottom: 0.5rem;
    }
    
    .step-active .step-number {
        background: #3b82f6;
        color: white;
    }
    
    .step-complete .step-number {
        background: #10b981;
        color: white;
    }
    
    .step-title {
        font-size: 0.875rem;
        color: #6b7280;
    }
    
    .step-active .step-title {
        color: #1f2937;
        font-weight: 600;
    }
    
    /* Info box */
    .info-box {
        background: #eff6ff;
        border: 1px solid #bfdbfe;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    .info-box h4 {
        color: #1e40af;
        margin: 0 0 0.5rem 0;
    }
    
    /* Action buttons */
    .stButton > button {
        width: 100%;
        border-radius: 6px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Document upload area */
    .upload-zone {
        border: 2px dashed #d1d5db;
        border-radius: 8px;
        padding: 2rem;
        text-align: center;
        background: #f9fafb;
        transition: all 0.2s;
    }
    
    .upload-zone:hover {
        border-color: #3b82f6;
        background: #eff6ff;
    }
    
    /* Results card */
    .result-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    
    .result-card h3 {
        margin: 0 0 1rem 0;
        color: #1f2937;
    }
    
    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 1rem 0;
    }
    
    .metric {
        flex: 1;
        background: #f9fafb;
        padding: 1rem;
        border-radius: 6px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #1f2937;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: #6b7280;
        margin-top: 0.25rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'application_id' not in st.session_state:
    st.session_state.application_id = None
if 'applicant_name' not in st.session_state:
    st.session_state.applicant_name = None
if 'current_step' not in st.session_state:
    st.session_state.current_step = 1
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'uploaded_files' not in st.session_state:
    st.session_state.uploaded_files = []


# ========== Helper Functions ==========

def create_application(name: str) -> Optional[str]:
    """Create new application"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/create",
            data={"applicant_name": name},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data['application_id']
    except requests.exceptions.ConnectionError:
        st.error("❌ **Cannot connect to server**. Please ensure the API is running on port 8000.")
        return None
    except Exception as e:
        st.error(f"❌ Error creating application: {e}")
        return None


def upload_documents(application_id: str, files) -> bool:
    """Upload documents"""
    try:
        files_data = [("documents", (file.name, file, file.type)) for file in files]
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/upload",
            files=files_data,
            timeout=30
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"❌ Upload failed: {e}")
        return False


def process_application(application_id: str) -> bool:
    """Process application"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/process",
            timeout=120
        )
        response.raise_for_status()
        return True
    except Exception as e:
        st.error(f"❌ Processing failed: {e}")
        return False


def get_application_status(application_id: str) -> Optional[Dict]:
    """Get status"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/applications/{application_id}/status",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except:
        return None


def get_application_results(application_id: str) -> Optional[Dict]:
    """Get results"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/applications/{application_id}/results",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except:
        return None


def chat_with_agent(application_id: str, query: str) -> Optional[str]:
    """Send chat query"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/applications/{application_id}/chat",
            json={
                "application_id": application_id,
                "query": query,
                "query_type": "explanation"
            },
            timeout=180  # Increased from 30s - LLM can take 60-120s to generate responses
        )
        response.raise_for_status()
        data = response.json()
        return data.get('response')
    except requests.exceptions.Timeout:
        st.error("Request timed out. The AI is taking longer than expected. Please try again.")
        return None
    except requests.exceptions.ConnectionError as e:
        st.error(f"Connection error: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None


# ========== Main UI ==========

# Professional Header
st.markdown("""
<div class="app-header">
    <h1>🇦🇪 UAE Social Support Portal</h1>
    <p>Empowering UAE Residents Through AI-Powered Support Services</p>
</div>
""", unsafe_allow_html=True)

# Sidebar - Application Status
with st.sidebar:
    st.markdown("### Application Status")
    
    if st.session_state.application_id:
        st.success(f"**ID:** {st.session_state.application_id}")
        st.info(f"**Applicant:** {st.session_state.applicant_name}")
        
        # Get current status
        status = get_application_status(st.session_state.application_id)
        if status:
            stage = status.get('current_stage', 'unknown')
            progress = status.get('progress_percentage', 0)
            
            # Calculate progress based on current step if not available from API
            if progress == 0 and st.session_state.current_step > 1:
                progress = (st.session_state.current_step - 1) * 25
            if st.session_state.current_step == 4:
                progress = 100
            
            st.progress(progress / 100)
            st.caption(f"Progress: {progress}%")
            
            # Show stage with icon
            stage_icons = {
                'pending': '',
                'extracting': '',
                'validating': '',
                'checking_eligibility': '',
                'generating_recommendation': '',
                'completed': '',
                'failed': ''
            }
            icon = stage_icons.get(stage, '')
            status_text = stage.replace('_', ' ').title()
            st.markdown(f"**Status:** {status_text}")
        
        if st.button("Refresh Status", use_container_width=True):
            st.rerun()
        
        if st.button("Start New Application", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    else:
        st.warning("No active application")
    
    st.divider()
    
    # Help section
    with st.expander("❓ Need Help?"):
        st.markdown("""
        **Quick Guide:**
        1. Enter your full name
        2. Upload required documents
        3. Click Process & Review
        4. View results & chat with AI
        
        **Support:** support@uae-social.gov.ae
        """)

# Progress Steps
if st.session_state.application_id:
    current_step = st.session_state.current_step
    
    cols = st.columns(4)
    steps = [
        ("1", "Create Application"),
        ("2", "Upload Documents"),
        ("3", "Processing"),
        ("4", "Results")
    ]
    
    for idx, (col, (num, title)) in enumerate(zip(cols, steps), 1):
        with col:
            if idx < current_step:
                st.markdown(f"""
                <div class="step step-complete">
                    <div class="step-number">✓</div>
                    <div class="step-title">{title}</div>
                </div>
                """, unsafe_allow_html=True)
            elif idx == current_step:
                st.markdown(f"""
                <div class="step step-active">
                    <div class="step-number">{num}</div>
                    <div class="step-title"><strong>{title}</strong></div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="step">
                    <div class="step-number">{num}</div>
                    <div class="step-title">{title}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()

# Main Content Area
if not st.session_state.application_id:
    # STEP 1: Create Application
    st.markdown("## Welcome! Let's Start Your Application")
    
    st.markdown("""
    <div class="info-box">
        <h4>What You'll Need:</h4>
        <ul>
            <li>Emirates ID (front image)</li>
            <li>Bank Statement (last 3-6 months, PDF)</li>
            <li>Resume/CV (PDF or image)</li>
            <li>Assets & Liabilities statement (Excel/PDF)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("create_application"):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            applicant_name = st.text_input(
                "Full Name (as per Emirates ID) *",
                placeholder="Enter your complete legal name",
                help="This must match your Emirates ID exactly"
            )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        with col2:
            submitted = st.form_submit_button("Create Application", type="primary", use_container_width=True)
        
        if submitted:
            if not applicant_name or len(applicant_name.strip()) < 3:
                st.error("Please enter your full legal name (minimum 3 characters)")
            else:
                with st.spinner("Creating your application..."):
                    app_id = create_application(applicant_name.strip())
                    if app_id:
                        st.session_state.application_id = app_id
                        st.session_state.applicant_name = applicant_name.strip()
                        st.session_state.current_step = 2
                        st.success(f"Application created! ID: {app_id}")
                        time.sleep(1)
                        st.rerun()

elif st.session_state.current_step == 2:
    # STEP 2: Upload Documents
    st.markdown("## Upload Your Documents")
    
    st.markdown("""
    <div class="info-box">
        <h4>Document Requirements:</h4>
        <ul>
            <li><strong>Emirates ID:</strong> Clear photo showing all details</li>
            <li><strong>Bank Statement:</strong> PDF from your bank (3-6 months)</li>
            <li><strong>Resume:</strong> Current CV in PDF format</li>
            <li><strong>Financial Statement:</strong> Assets & liabilities (Excel/PDF)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_files = st.file_uploader(
        "📎 Select Documents to Upload",
        type=['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls'],
        accept_multiple_files=True,
        help="You can select multiple files at once"
    )
    
    if uploaded_files:
        st.markdown("### Selected Files:")
        for file in uploaded_files:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.text(f"{file.name}")
            with col2:
                st.text(f"{file.size / 1024:.1f} KB")
            with col3:
                st.text(file.type.split('/')[-1].upper())
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if uploaded_files and st.button("Upload Documents", type="primary", use_container_width=True):
            with st.spinner(f"Uploading {len(uploaded_files)} file(s)..."):
                if upload_documents(st.session_state.application_id, uploaded_files):
                    st.session_state.uploaded_files = [f.name for f in uploaded_files]
                    st.success(f"Successfully uploaded {len(uploaded_files)} document(s)!")
                    time.sleep(1)
    
    if st.session_state.uploaded_files:
        st.markdown("---")
        st.markdown("### Uploaded Documents:")
        for filename in st.session_state.uploaded_files:
            st.text(f"{filename}")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("Process Application", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.rerun()

elif st.session_state.current_step == 3:
    # STEP 3: Processing
    st.markdown("## Processing Your Application")
    
    status = get_application_status(st.session_state.application_id)
    
    if status:
        stage = status.get('current_stage', 'pending')
        progress = status.get('progress_percentage', 0)
        
        # Processing animation
        if stage not in ['completed', 'failed']:
            with st.spinner(""):
                st.markdown(f"""
                <div class="status-card status-processing">
                    <h3>🔄 Processing in progress...</h3>
                    <p><strong>Current Stage:</strong> {stage.replace('_', ' ').title()}</p>
                    <p>Your application is being analyzed by our AI system. This may take 30-60 seconds.</p>
                </div>
                """, unsafe_allow_html=True)
                
                progress_bar = st.progress(progress / 100)
                status_text = st.empty()
                
                # Start processing if not started
                if stage == 'pending':
                    process_application(st.session_state.application_id)
                
                # Auto-refresh every 2 seconds
                for i in range(30):
                    time.sleep(2)
                    status = get_application_status(st.session_state.application_id)
                    if status:
                        new_stage = status.get('current_stage')
                        new_progress = status.get('progress_percentage', 0)
                        progress_bar.progress(new_progress / 100)
                        status_text.text(f"Stage: {new_stage.replace('_', ' ').title()}")
                        
                        if new_stage in ['completed', 'failed']:
                            break
                
                st.rerun()
        
        elif stage == 'completed':
            st.markdown("""
            <div class="status-card status-success">
                <h2>Processing Complete!</h2>
                <p>Your application has been successfully processed. View your results below.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.current_step = 4
            st.session_state.processing_complete = True
            
            if st.button("View Results", type="primary", use_container_width=True):
                st.rerun()
        
        elif stage == 'failed':
            st.markdown("""
            <div class="status-card status-error">
                <h3>Processing Failed</h3>
                <p>There was an error processing your application. Please check your documents and try again.</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("🔄 Try Again", use_container_width=True):
                st.session_state.current_step = 2
                st.rerun()

elif st.session_state.current_step == 4:
    # STEP 4: Results & Chatbot
    results = get_application_results(st.session_state.application_id)
    
    if results:
        # Decision Banner
        recommendation = results.get('recommendation', {})
        decision = recommendation.get('decision', 'pending')
        support_amount = recommendation.get('support_amount', 0)
        
        if decision == 'APPROVED':
            st.markdown(f"""
            <div class="status-card status-success">
                <h1>Congratulations! Application APPROVED</h1>
                <h2>Monthly Support: AED {support_amount:,.2f}</h2>
                <p>You are eligible for financial assistance and enablement programs.</p>
            </div>
            """, unsafe_allow_html=True)
        elif decision == 'SOFT_DECLINED':
            st.markdown(f"""
            <div class="status-card status-warning">
                <h2>Application Soft Declined</h2>
                <h3>Support Available: AED {support_amount:,.2f}</h3>
                <p>While full support isn't available now, you qualify for enablement programs and transitional assistance.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card status-error">
                <h2>Application Not Approved</h2>
                <p>Unfortunately, you don't currently meet the eligibility criteria. Review the feedback below and consider reapplying.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Tabs for detailed information
        tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Validation", "Programs", "AI Assistant"])
        
        with tab1:
            st.markdown("### Financial Overview")
            
            # Extract key metrics
            extracted = results.get('extracted_data', {})
            income_data = extracted.get('income_data', {})
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Monthly Income", f"AED {income_data.get('monthly_income', 0):,.0f}")
            with col2:
                st.metric("Monthly Expenses", f"AED {income_data.get('monthly_expenses', 0):,.0f}")
            with col3:
                eligibility = results.get('eligibility', {})
                st.metric("Eligibility Score", f"{eligibility.get('eligibility_score', 0):.0%}")
            with col4:
                st.metric("Support Amount", f"AED {support_amount:,.0f}")
            
            # Reasoning
            st.markdown("### Decision Reasoning")
            reasoning = recommendation.get('reasoning', 'No reasoning provided')
            st.markdown(reasoning)
        
        with tab2:
            st.markdown("### Validation Report")
            
            validation = results.get('validation', {})
            is_valid = validation.get('is_valid', False)
            issues = validation.get('issues', [])
            
            if is_valid:
                st.success("All documents validated successfully")
            else:
                st.warning(f"{len(issues)} validation issue(s) found")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Completeness", f"{validation.get('completeness_score', 0):.0%}")
            with col2:
                st.metric("Confidence", f"{validation.get('confidence_score', 0):.0%}")
            
            if issues:
                st.markdown("#### Issues Detected:")
                for issue in issues:
                    severity_icon = {"critical": "[CRITICAL]", "warning": "[WARNING]", "info": "[INFO]"}.get(issue['severity'], "")
                    with st.expander(f"{severity_icon} {issue['field']}"):
                        st.write(f"**Message:** {issue['message']}")
                        if issue.get('suggested_resolution'):
                            st.info(f"**Suggestion:** {issue['suggested_resolution']}")
        
        with tab3:
            st.markdown("### Recommended Programs")
            
            programs = recommendation.get('programs', [])
            
            if programs:
                for program in programs:
                    priority_colors = {"high": "[HIGH]", "medium": "[MEDIUM]", "low": "[LOW]"}
                    priority = program.get('priority', 'medium')
                    
                    with st.expander(f"{priority_colors.get(priority, '')} {program.get('name', 'Program')}"):
                        st.write(f"**Category:** {program.get('category', 'N/A')}")
                        st.write(f"**Description:** {program.get('description', 'No description')}")
                        st.write(f"**Duration:** {program.get('duration', 'N/A')}")
                        if program.get('benefits'):
                            st.write(f"**Benefits:** {program['benefits']}")
            else:
                st.info("No specific programs recommended at this time.")
        
        with tab4:
            st.markdown("### AI Assistant")
            
            st.info("Ask me anything about your application, decision, or how to improve!")
            
            # Chat history display
            chat_container = st.container()
            with chat_container:
                if st.session_state.chat_history:
                    for msg in st.session_state.chat_history:
                        if msg['role'] == 'user':
                            st.markdown(f"**You:** {msg['content']}")
                        else:
                            st.markdown(f"**AI Assistant:** {msg['content']}")
                        st.markdown("---")
                else:
                    st.info("Start by asking a question or use the quick questions below!")
            
            # Quick action buttons
            st.markdown("##### Quick Questions:")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("Why this decision?", use_container_width=True, key="quick_why"):
                    query = "Why was I approved/declined? Explain in detail."
                    with st.spinner("AI is analyzing your application... This may take up to 2 minutes."):
                        response = chat_with_agent(st.session_state.application_id, query)
                        if response:
                            st.session_state.chat_history.append({"role": "user", "content": query})
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                            st.rerun()
            
            with col2:
                if st.button("How to improve?", use_container_width=True, key="quick_improve"):
                    query = "What can I do to improve my chances next time?"
                    with st.spinner("AI is analyzing your application... This may take up to 2 minutes."):
                        response = chat_with_agent(st.session_state.application_id, query)
                        if response:
                            st.session_state.chat_history.append({"role": "user", "content": query})
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                            st.rerun()
            
            with col3:
                if st.button("Check details", use_container_width=True, key="quick_details"):
                    query = "Show me the key factors in my application"
                    with st.spinner("AI is analyzing your application... This may take up to 2 minutes."):
                        response = chat_with_agent(st.session_state.application_id, query)
                        if response:
                            st.session_state.chat_history.append({"role": "user", "content": query})
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                            st.rerun()
            
            # Chat input with form to handle submission properly
            with st.form(key="chat_form", clear_on_submit=True):
                user_query = st.text_input("Ask your question:", placeholder="Type your question here...", key="chat_input")
                submit_chat = st.form_submit_button("Send", use_container_width=True, type="primary")
                
                if submit_chat and user_query.strip():
                    with st.spinner("AI is analyzing your question... This may take up to 2 minutes for complex queries."):
                        response = chat_with_agent(st.session_state.application_id, user_query)
                        if response:
                            st.session_state.chat_history.append({"role": "user", "content": user_query})
                            st.session_state.chat_history.append({"role": "assistant", "content": response})
                            st.rerun()
                        else:
                            st.error("Failed to get response from AI. Please try a simpler question or try again later.")
    else:
        st.error("Unable to load results")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 2rem 0;'>
    <p><strong>UAE Social Support Portal</strong></p>
    <p>Powered by AI • Secure • Confidential</p>
    <p><small>© 2026 UAE Government. All rights reserved.</small></p>
</div>
""", unsafe_allow_html=True)
