"""
Social Support AI Application - Streamlit Frontend
Interactive chatbot interface for application submission and tracking
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, Any, List
import io
from PIL import Image

# Page configuration
st.set_page_config(
    page_title="Social Support AI Assistant",
    page_icon="🤝",
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
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
        display: flex;
        flex-direction: column;
    }
    .user-message {
        background-color: #e3f2fd;
        margin-left: 20%;
    }
    .assistant-message {
        background-color: #f5f5f5;
        margin-right: 20%;
    }
    .status-box {
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .status-approved {
        background-color: #c8e6c9;
        border-left: 4px solid #4caf50;
    }
    .status-pending {
        background-color: #fff9c4;
        border-left: 4px solid #ffc107;
    }
    .status-declined {
        background-color: #ffcdd2;
        border-left: 4px solid #f44336;
    }
    .metric-card {
        background-color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
API_BASE_URL = "http://localhost:8000"

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "application_id" not in st.session_state:
    st.session_state.application_id = None
if "application_data" not in st.session_state:
    st.session_state.application_data = {}
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = {}
if "current_step" not in st.session_state:
    st.session_state.current_step = "welcome"


def display_message(role: str, content: str):
    """Display a chat message"""
    css_class = "user-message" if role == "user" else "assistant-message"
    icon = "👤" if role == "user" else "🤖"
    
    st.markdown(f"""
    <div class="chat-message {css_class}">
        <div style="font-weight: bold; margin-bottom: 0.5rem;">
            {icon} {role.capitalize()}
        </div>
        <div>{content}</div>
    </div>
    """, unsafe_allow_html=True)


def call_api(endpoint: str, method: str = "GET", data: Dict = None, files: Dict = None) -> Dict:
    """Make API calls to FastAPI backend"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method == "POST":
            if files:
                response = requests.post(url, data=data, files=files)
            else:
                response = requests.post(url, json=data)
        else:
            response = requests.get(url)
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return {"error": str(e)}


def main():
    """Main application"""
    
    # Header
    st.markdown('<div class="main-header">🤝 Social Support AI Assistant</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Automated Application Processing in Minutes</div>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/300x100/1f77b4/ffffff?text=Government+Services", width=True)
        
        st.markdown("### 📋 Application Process")
        
        steps = [
            ("1️⃣", "Personal Information", st.session_state.current_step in ["welcome", "personal_info"]),
            ("2️⃣", "Document Upload", st.session_state.current_step == "documents"),
            ("3️⃣", "AI Processing", st.session_state.current_step == "processing"),
            ("4️⃣", "Decision & Recommendations", st.session_state.current_step == "complete")
        ]
        
        for icon, step_name, is_current in steps:
            if is_current:
                st.markdown(f"**{icon} {step_name}** ✓")
            else:
                st.markdown(f"{icon} {step_name}")
        
        st.markdown("---")
        
        if st.session_state.application_id:
            st.markdown(f"**Application ID:**")
            st.code(st.session_state.application_id)
        
        st.markdown("---")
        st.markdown("### 💡 Key Features")
        st.markdown("""
        - ⚡ **5-minute processing**
        - 🤖 **99% automation**
        - 🔍 **AI-powered validation**
        - 📊 **Transparent decisions**
        - 🎓 **Personalized recommendations**
        """)
        
        st.markdown("---")
        st.markdown("### 📞 Need Help?")
        st.markdown("Contact: support@gov.ae")
        
        if st.button("🔄 Start New Application", use_container_width=True):
            st.session_state.messages = []
            st.session_state.application_id = None
            st.session_state.application_data = {}
            st.session_state.uploaded_files = {}
            st.session_state.current_step = "welcome"
            st.rerun()
    
    # Main content area
    main_container = st.container()
    
    with main_container:
        # Display chat history
        chat_container = st.container()
        with chat_container:
            if len(st.session_state.messages) == 0:
                # Welcome message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": """👋 Welcome to the Social Support AI Assistant!

I'm here to help you apply for financial and economic enablement support. The process is simple:

1. **Share your information** through our interactive form
2. **Upload required documents** (Emirates ID, Bank Statement, Resume, etc.)
3. **AI processing** - I'll analyze your application in minutes
4. **Receive your decision** with personalized recommendations

Let's get started! Please provide your basic information below."""
                })
            
            for message in st.session_state.messages:
                display_message(message["role"], message["content"])
        
        # Input area based on current step
        if st.session_state.current_step == "welcome":
            show_personal_info_form()
        
        elif st.session_state.current_step == "personal_info":
            show_document_upload()
        
        elif st.session_state.current_step == "documents":
            show_processing_status()
        
        elif st.session_state.current_step == "processing":
            show_processing_status()
        
        elif st.session_state.current_step == "complete":
            show_results()


def show_personal_info_form():
    """Display personal information form"""
    st.markdown("### 📝 Personal Information")
    
    with st.form("personal_info_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            full_name = st.text_input("Full Name *", placeholder="John Doe")
            emirates_id = st.text_input("Emirates ID *", placeholder="784-XXXX-XXXXXXX-X")
            phone = st.text_input("Phone Number *", placeholder="+971 XX XXX XXXX")
            email = st.text_input("Email Address *", placeholder="john.doe@email.com")
        
        with col2:
            date_of_birth = st.date_input("Date of Birth *")
            gender = st.selectbox("Gender *", ["Male", "Female", "Other"])
            marital_status = st.selectbox("Marital Status *", ["Single", "Married", "Divorced", "Widowed"])
            family_size = st.number_input("Family Size *", min_value=1, max_value=20, value=1)
        
        st.markdown("#### Employment Information")
        
        col3, col4 = st.columns(2)
        
        with col3:
            employment_status = st.selectbox(
                "Employment Status *",
                ["Employed", "Unemployed", "Self-Employed", "Student", "Retired"]
            )
            monthly_income = st.number_input("Monthly Income (AED) *", min_value=0, value=0, step=500)
        
        with col4:
            education_level = st.selectbox(
                "Education Level *",
                ["High School", "Diploma", "Bachelor's Degree", "Master's Degree", "PhD"]
            )
            has_disability = st.checkbox("Do you have any disability?")
        
        st.markdown("#### Additional Information")
        reason_for_support = st.text_area(
            "Reason for Support Request *",
            placeholder="Please describe your situation and why you need support..."
        )
        
        submit_button = st.form_submit_button("Continue to Document Upload ➡️", use_container_width=True)
        
        if submit_button:
            # Validate required fields
            if not all([full_name, emirates_id, phone, email]):
                st.error("Please fill in all required fields marked with *")
                return
            
            # Save to session state
            st.session_state.application_data = {
                "full_name": full_name,
                "emirates_id": emirates_id,
                "phone": phone,
                "email": email,
                "date_of_birth": date_of_birth.isoformat(),
                "gender": gender,
                "marital_status": marital_status,
                "family_size": family_size,
                "employment_status": employment_status,
                "monthly_income": monthly_income,
                "education_level": education_level,
                "has_disability": has_disability,
                "reason_for_support": reason_for_support
            }
            
            st.session_state.messages.append({
                "role": "user",
                "content": f"Submitted personal information for {full_name}"
            })
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": """✅ Thank you! Your personal information has been recorded.

Now, please upload the required documents:
- 📄 Emirates ID (both sides)
- 🏦 Bank Statement (last 3 months)
- 📋 Resume/CV
- 📊 Assets & Liabilities (Excel format)
- 📈 Credit Report (if available)

These documents help us assess your application accurately."""
            })
            
            st.session_state.current_step = "personal_info"
            st.rerun()


def show_document_upload():
    """Display document upload interface"""
    st.markdown("### 📎 Document Upload")
    st.markdown("Please upload the following documents:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        emirates_id_file = st.file_uploader(
            "📄 Emirates ID (Image/PDF) *",
            type=["jpg", "jpeg", "png", "pdf"],
            key="emirates_id"
        )
        
        bank_statement_file = st.file_uploader(
            "🏦 Bank Statement (PDF) *",
            type=["pdf"],
            key="bank_statement"
        )
        
        resume_file = st.file_uploader(
            "📋 Resume/CV (PDF/DOCX) *",
            type=["pdf", "docx"],
            key="resume"
        )
    
    with col2:
        assets_file = st.file_uploader(
            "📊 Assets & Liabilities (Excel) *",
            type=["xlsx", "xls"],
            key="assets"
        )
        
        credit_report_file = st.file_uploader(
            "📈 Credit Report (PDF)",
            type=["pdf"],
            key="credit_report",
            help="Optional but recommended"
        )
    
    st.markdown("---")
    
    col_back, col_submit = st.columns([1, 3])
    
    with col_back:
        if st.button("⬅️ Back", use_container_width=True):
            st.session_state.current_step = "welcome"
            st.rerun()
    
    with col_submit:
        if st.button("🚀 Submit Application", type="primary", use_container_width=True):
            # Validate required uploads
            required_files = {
                "emirates_id": emirates_id_file,
                "bank_statement": bank_statement_file,
                "resume": resume_file,
                "assets": assets_file
            }
            
            if not all(required_files.values()):
                st.error("Please upload all required documents (marked with *)")
                return
            
            # Prepare files for upload
            st.session_state.uploaded_files = {
                "emirates_id": emirates_id_file.read(),
                "bank_statement": bank_statement_file.read(),
                "resume": resume_file.read(),
                "assets": assets_file.read()
            }
            
            if credit_report_file:
                st.session_state.uploaded_files["credit_report"] = credit_report_file.read()
            
            st.session_state.messages.append({
                "role": "user",
                "content": f"Uploaded {len(st.session_state.uploaded_files)} documents"
            })
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": """📤 All documents received! Processing your application...

🤖 AI Workflow Started:
1. ✓ Extracting data from documents
2. ⏳ Validating information
3. ⏳ Assessing eligibility
4. ⏳ Making decision
5. ⏳ Generating recommendations

This typically takes 2-5 minutes. Please wait..."""
            })
            
            st.session_state.current_step = "documents"
            st.rerun()


def show_processing_status():
    """Show processing status with progress"""
    st.markdown("### ⚙️ Processing Your Application")
    
    # Create progress indicator
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate API call to process application
    with st.spinner("AI agents are analyzing your application..."):
        try:
            # Call API
            response = call_api(
                "/api/v1/applications/submit",
                method="POST",
                data={
                    "form_data": st.session_state.application_data,
                    "files": {k: "base64_encoded" for k in st.session_state.uploaded_files.keys()}
                }
            )
            
            if "error" in response:
                st.error("Processing failed. Please try again.")
                return
            
            # Update progress
            progress_bar.progress(100)
            st.session_state.application_id = response.get("application_id", "APP-" + datetime.now().strftime("%Y%m%d%H%M%S"))
            st.session_state.application_result = response
            
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"""✅ Processing Complete!

**Application ID:** {st.session_state.application_id}

Your application has been processed successfully. Click below to view your results."""
            })
            
            st.session_state.current_step = "complete"
            st.rerun()
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            progress_bar.progress(0)


def show_results():
    """Display application results and recommendations"""
    st.markdown("### 🎯 Application Results")
    
    # Mock results (replace with actual API response)
    decision = "approved"  # or "soft_decline" or "manual_review"
    confidence = 0.92
    processing_time = 3.45
    
    # Decision card
    if decision == "approved":
        st.markdown(f"""
        <div class="status-box status-approved">
            <h2>✅ Application Approved</h2>
            <p><strong>Confidence Score:</strong> {confidence:.1%}</p>
            <p><strong>Processing Time:</strong> {processing_time:.2f} seconds</p>
            <p>Congratulations! Your application has been approved for social support.</p>
        </div>
        """, unsafe_allow_html=True)
    elif decision == "soft_decline":
        st.markdown(f"""
        <div class="status-box status-declined">
            <h2>ℹ️ Application Requires Review</h2>
            <p><strong>Confidence Score:</strong> {confidence:.1%}</p>
            <p>Your application needs additional review. We've identified opportunities to improve your eligibility.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="status-box status-pending">
            <h2>⏳ Manual Review Required</h2>
            <p>Your application requires human review. We'll contact you within 2 business days.</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Metrics
    st.markdown("### 📊 Assessment Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Eligibility Score", "92%", "12%")
    with col2:
        st.metric("Risk Assessment", "Low", "Safe")
    with col3:
        st.metric("Data Quality", "98%", "Excellent")
    with col4:
        st.metric("Fraud Score", "2%", "-18%")
    
    # Explainability
    st.markdown("### 🔍 Decision Factors")
    st.markdown("""
    The decision was based on the following factors:
    
    - ✅ **Income Level**: Meets eligibility criteria
    - ✅ **Family Size**: Qualifies for family support
    - ✅ **Employment History**: Stable employment record
    - ⚠️ **Credit Score**: Could be improved
    - ✅ **Documentation**: All required documents submitted
    """)
    
    # Recommendations
    st.markdown("### 🎓 Personalized Recommendations")
    
    tab1, tab2, tab3 = st.tabs(["💼 Job Opportunities", "📚 Upskilling Programs", "💡 Career Counseling"])
    
    with tab1:
        st.markdown("#### Matched Job Opportunities")
        jobs = [
            {"title": "Customer Service Representative", "company": "Emirates Group", "match": "95%"},
            {"title": "Administrative Assistant", "company": "Dubai Municipality", "match": "88%"},
            {"title": "Sales Associate", "company": "Majid Al Futtaim", "match": "82%"}
        ]
        
        for job in jobs:
            with st.expander(f"**{job['title']}** at {job['company']} - {job['match']} Match"):
                st.markdown(f"""
                - **Location**: Dubai
                - **Salary Range**: AED 4,000 - 6,000
                - **Type**: Full-time
                - **Requirements**: High School, 2+ years experience
                
                [Apply Now →](#)
                """)
    
    with tab2:
        st.markdown("#### Recommended Training Programs")
        programs = [
            {"name": "Digital Marketing Fundamentals", "duration": "6 weeks", "cost": "Free"},
            {"name": "Customer Service Excellence", "duration": "4 weeks", "cost": "Free"},
            {"name": "Microsoft Office Specialist", "duration": "8 weeks", "cost": "Subsidized"}
        ]
        
        for program in programs:
            with st.expander(f"**{program['name']}** - {program['duration']}"):
                st.markdown(f"""
                - **Duration**: {program['duration']}
                - **Cost**: {program['cost']}
                - **Format**: Online + In-person
                - **Certificate**: Yes
                
                [Enroll Now →](#)
                """)
    
    with tab3:
        st.markdown("#### Career Development Support")
        st.markdown("""
        Based on your profile, we recommend:
        
        1. **Resume Review Session** - Get professional feedback on your CV
        2. **Interview Preparation** - Practice with career counselors
        3. **Industry Networking Events** - Connect with potential employers
        4. **Skills Assessment** - Identify your strengths and development areas
        
        **Next Step**: Schedule a counseling session with our career advisors.
        """)
        
        if st.button("📅 Schedule Counseling Session", type="primary", use_container_width=True):
            st.success("Counseling session request submitted! We'll contact you within 24 hours.")
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📥 Download Full Report", use_container_width=True):
            st.info("Report generation coming soon!")
    
    with col2:
        if st.button("📧 Email Results", use_container_width=True):
            st.success("Results sent to your email!")
    
    with col3:
        if st.button("🆕 New Application", use_container_width=True):
            st.session_state.messages = []
            st.session_state.application_id = None
            st.session_state.application_data = {}
            st.session_state.uploaded_files = {}
            st.session_state.current_step = "welcome"
            st.rerun()


if __name__ == "__main__":
    main()