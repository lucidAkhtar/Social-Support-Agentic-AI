"""
Applicant Portal - Enhanced User Journey
Production-grade UI with seamless flow and real-time updates
"""

import streamlit as st
import requests
import time
from typing import Optional, Dict, Any
import json

# API Configuration
API_BASE_URL = "http://localhost:8000"

def show():
    """Main applicant portal interface"""
    
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
    if 'auto_refresh' not in st.session_state:
        st.session_state.auto_refresh = False
    
    # Header
    st.markdown("""
    <div class="app-header">
        <h1>👤 Application Portal</h1>
        <p>Submit your application and track its progress in real-time</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Progress indicator
    if st.session_state.application_id:
        show_progress_tracker()
    
    # Route to appropriate step
    if not st.session_state.application_id:
        show_step1_create_application()
    elif st.session_state.current_step == 2:
        show_step2_upload_documents()
    elif st.session_state.current_step == 3:
        show_step3_processing()
    elif st.session_state.current_step == 4:
        show_step4_results()


def show_progress_tracker():
    """Visual progress tracker"""
    st.markdown("### 📍 Application Progress")
    
    current_step = st.session_state.current_step
    steps = [
        ("📝", "Create", 1),
        ("📄", "Upload", 2),
        ("⚙️", "Process", 3),
        ("✅", "Results", 4)
    ]
    
    cols = st.columns(len(steps))
    for col, (icon, title, step_num) in zip(cols, steps):
        with col:
            if step_num < current_step:
                st.markdown(f"""
                <div style='text-align: center; opacity: 0.6;'>
                    <div style='font-size: 2rem;'>{icon}</div>
                    <div style='color: #10b981; font-weight: 600;'>✓ {title}</div>
                </div>
                """, unsafe_allow_html=True)
            elif step_num == current_step:
                st.markdown(f"""
                <div style='text-align: center;'>
                    <div style='font-size: 2rem; animation: pulse 2s infinite;'>{icon}</div>
                    <div style='color: #0066cc; font-weight: 700;'>► {title}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='text-align: center; opacity: 0.3;'>
                    <div style='font-size: 2rem;'>{icon}</div>
                    <div>{title}</div>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()
    
    # Show application info
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        st.caption(f"**Application ID:** `{st.session_state.application_id}`")
    with col2:
        st.caption(f"**Applicant:** {st.session_state.applicant_name}")
    with col3:
        if st.button("🗑️ Reset", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['page', 'user_role']:
                    del st.session_state[key]
            st.rerun()


def show_step1_create_application():
    """Step 1: Create application"""
    st.markdown("## 🚀 Let's Get Started!")
    
    st.markdown("""
    <div style='background: #eff6ff; border-left: 4px solid #3b82f6; padding: 1rem; border-radius: 4px; margin: 1rem 0;'>
        <h4 style='margin: 0 0 0.5rem 0; color: #1e40af;'>📋 What You'll Need:</h4>
        <ul style='margin: 0;'>
            <li><strong>Emirates ID</strong> - Clear photo (front side)</li>
            <li><strong>Bank Statement</strong> - Last 3-6 months (PDF)</li>
            <li><strong>Resume/CV</strong> - Current employment history</li>
            <li><strong>Financial Statement</strong> - Assets & liabilities (Excel/PDF)</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("create_application"):
        st.markdown("### 👤 Your Information")
        
        col1, col2 = st.columns(2)
        with col1:
            applicant_name = st.text_input(
                "Full Name (as per Emirates ID) *",
                placeholder="Enter your complete legal name",
                help="Must match your official documents exactly"
            )
        with col2:
            email = st.text_input(
                "Email Address (optional)",
                placeholder="your.email@example.com",
                help="For application updates and notifications"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            phone = st.text_input(
                "Phone Number (optional)",
                placeholder="+971 XX XXX XXXX",
                help="For urgent communications"
            )
        with col2:
            emirates_id = st.text_input(
                "Emirates ID Number (optional)",
                placeholder="784-XXXX-XXXXXXX-X",
                help="Optional for pre-validation"
            )
        
        st.divider()
        
        # Terms and conditions
        agree = st.checkbox(
            "I confirm that all information provided is accurate and I consent to data processing for eligibility assessment.",
            value=False
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            submitted = st.form_submit_button(
                "✨ Create Application",
                type="primary",
                use_container_width=True,
                disabled=not agree
            )
        
        if submitted:
            if not applicant_name or len(applicant_name.strip()) < 3:
                st.error("⚠️ Please enter your full legal name (minimum 3 characters)")
            elif not agree:
                st.error("⚠️ Please accept the terms and conditions to proceed")
            else:
                with st.spinner("Creating your application..."):
                    app_id = create_application(applicant_name.strip())
                    if app_id:
                        st.session_state.application_id = app_id
                        st.session_state.applicant_name = applicant_name.strip()
                        st.session_state.current_step = 2
                        st.success(f"✅ Application created successfully!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()


def show_step2_upload_documents():
    """Step 2: Upload documents"""
    st.markdown("## 📄 Upload Your Documents")
    
    st.markdown("""
    <div style='background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; border-radius: 4px; margin: 1rem 0;'>
        <h4 style='margin: 0 0 0.5rem 0; color: #92400e;'>💡 Tips for Better Results:</h4>
        <ul style='margin: 0;'>
            <li>Ensure documents are clear and readable</li>
            <li>Use PDF format for bank statements and financial documents</li>
            <li>File names should be descriptive (e.g., "bank_statement_dec2025.pdf")</li>
            <li>Maximum file size: 10MB per document</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    # Document type selector
    doc_type = st.selectbox(
        "📋 Document Category",
        [
            "All Documents (Quick Upload)",
            "Emirates ID",
            "Bank Statement",
            "Resume/CV",
            "Assets & Liabilities",
            "Credit Report",
            "Employment Letter"
        ],
        help="Select category for automatic classification"
    )
    
    uploaded_files = st.file_uploader(
        "📎 Select Files to Upload",
        type=['pdf', 'jpg', 'jpeg', 'png', 'xlsx', 'xls'],
        accept_multiple_files=True,
        help="You can select multiple files at once"
    )
    
    if uploaded_files:
        st.markdown("### 📦 Selected Files")
        
        for file in uploaded_files:
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            with col1:
                st.text(f"📄 {file.name}")
            with col2:
                st.text(f"{file.size / 1024:.1f} KB")
            with col3:
                st.text(file.type.split('/')[-1].upper())
            with col4:
                st.markdown("✅")
        
        st.divider()
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("📤 Upload All Documents", type="primary", use_container_width=True):
                with st.spinner(f"Uploading {len(uploaded_files)} file(s)..."):
                    if upload_documents(st.session_state.application_id, uploaded_files):
                        st.session_state.uploaded_files = [f.name for f in uploaded_files]
                        st.success(f"✅ Successfully uploaded {len(uploaded_files)} document(s)!")
                        time.sleep(1)
    
    # Show uploaded files
    if st.session_state.uploaded_files:
        st.markdown("---")
        st.markdown("### ✅ Uploaded Documents")
        
        for filename in st.session_state.uploaded_files:
            st.markdown(f"✓ {filename}")
        
        st.markdown("""
        <div style='background: #d1fae5; border-left: 4px solid #10b981; padding: 1rem; border-radius: 4px; margin: 1rem 0;'>
            <h4 style='margin: 0; color: #065f46;'>✅ Ready to Process!</h4>
            <p style='margin: 0.5rem 0 0 0;'>All documents uploaded. Click below to start AI analysis.</p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🚀 Start Processing", type="primary", use_container_width=True):
                st.session_state.current_step = 3
                st.session_state.auto_refresh = True
                st.rerun()


def show_step3_processing():
    """Step 3: Processing with real-time updates"""
    st.markdown("## ⚙️ AI Analysis in Progress")
    
    # Get current status
    status = get_application_status(st.session_state.application_id)
    
    if status:
        stage = status.get('current_stage', 'pending')
        progress = status.get('progress_percentage', 0)
        
        # Start processing if not started
        if stage == 'pending':
            with st.spinner("Initializing AI agents..."):
                process_application(st.session_state.application_id)
                time.sleep(2)
                st.rerun()
        
        # Processing stages visualization
        stages_info = {
            'pending': ('⏳', 'Initializing', 'Setting up processing pipeline'),
            'extracting': ('🔍', 'Data Extraction', 'Using OCR and document parsing'),
            'validating': ('✅', 'Validation', 'Cross-checking document consistency'),
            'checking_eligibility': ('📊', 'Eligibility Check', 'Running ML model analysis'),
            'generating_recommendation': ('💡', 'Recommendations', 'Calculating support amount'),
            'completed': ('🎉', 'Completed', 'Application processed successfully'),
            'failed': ('❌', 'Failed', 'Error occurred during processing')
        }
        
        icon, title, description = stages_info.get(stage, ('📝', stage, ''))
        
        if stage not in ['completed', 'failed']:
            st.markdown(f"""
            <div style='background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%); 
                        padding: 2rem; border-radius: 10px; text-align: center; margin: 2rem 0;'>
                <div style='font-size: 4rem; margin-bottom: 1rem;'>{icon}</div>
                <h2 style='margin: 0; color: #1e40af;'>{title}</h2>
                <p style='margin: 0.5rem 0; color: #3b82f6;'>{description}</p>
                <p style='margin: 1rem 0 0 0; font-size: 0.875rem; color: #6b7280;'>
                    This typically takes 30-60 seconds
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress bar
            progress_bar = st.progress(progress / 100)
            col1, col2, col3 = st.columns(3)
            with col2:
                st.markdown(f"<div style='text-align: center; font-size: 1.5rem; font-weight: 700; color: #0066cc;'>{progress}%</div>", unsafe_allow_html=True)
            
            # Processing steps breakdown
            st.markdown("### 🔄 Processing Steps")
            steps = [
                ("Extract Documents", progress >= 20),
                ("Validate Data", progress >= 40),
                ("Check Eligibility", progress >= 60),
                ("Generate Recommendations", progress >= 80),
                ("Prepare Results", progress >= 95)
            ]
            
            for step_name, completed in steps:
                if completed:
                    st.markdown(f"✅ **{step_name}** - Complete")
                else:
                    st.markdown(f"⏳ {step_name} - Pending")
            
            # Auto-refresh
            if st.session_state.auto_refresh:
                time.sleep(3)
                st.rerun()
            
            if st.button("🔄 Refresh Status"):
                st.rerun()
        
        elif stage == 'completed':
            st.markdown("""
            <div style='background: linear-gradient(135deg, #d1fae5 0%, #ecfdf5 100%); 
                        padding: 2rem; border-radius: 10px; text-align: center; margin: 2rem 0;'>
                <div style='font-size: 4rem; margin-bottom: 1rem;'>🎉</div>
                <h1 style='margin: 0; color: #065f46;'>Processing Complete!</h1>
                <p style='margin: 1rem 0; color: #047857;'>
                    Your application has been successfully analyzed by our AI system.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.session_state.current_step = 4
            st.session_state.auto_refresh = False
            st.session_state.processing_complete = True
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                if st.button("📊 View Results", type="primary", use_container_width=True):
                    st.rerun()
        
        elif stage == 'failed':
            st.markdown("""
            <div style='background: #fee2e2; border-left: 4px solid #ef4444; padding: 1.5rem; border-radius: 4px;'>
                <h3 style='margin: 0; color: #991b1b;'>❌ Processing Failed</h3>
                <p style='margin: 0.5rem 0 0 0;'>There was an error processing your application. Please try again or contact support.</p>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔄 Retry Processing", use_container_width=True):
                    process_application(st.session_state.application_id)
                    st.rerun()
            with col2:
                if st.button("📄 Re-upload Documents", use_container_width=True):
                    st.session_state.current_step = 2
                    st.rerun()
            with col3:
                if st.button("💬 Contact Support", use_container_width=True):
                    st.info("Support: support@uae-social.gov.ae | Phone: 800-SUPPORT")


def show_step4_results():
    """Step 4: Results and chatbot"""
    results = get_application_results(st.session_state.application_id)
    
    if not results:
        st.error("❌ Unable to load results. Please try refreshing.")
        if st.button("🔄 Refresh"):
            st.rerun()
        return
    
    # Decision banner
    recommendation = results.get('recommendation', {})
    decision = recommendation.get('decision', 'pending')
    support_amount = recommendation.get('support_amount', 0)
    
    if decision == 'APPROVED':
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%); 
                    padding: 2.5rem; border-radius: 12px; text-align: center; margin: 2rem 0; 
                    box-shadow: 0 10px 30px rgba(16, 185, 129, 0.3);'>
            <div style='font-size: 5rem; margin-bottom: 1rem; animation: bounce 1s;'>🎉</div>
            <h1 style='margin: 0; color: #065f46; font-size: 2.5rem;'>Congratulations!</h1>
            <h2 style='margin: 1rem 0; color: #047857;'>Application APPROVED</h2>
            <div style='background: white; padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0; display: inline-block;'>
                <div style='color: #6b7280; font-size: 0.875rem;'>Monthly Support Amount</div>
                <div style='color: #065f46; font-size: 3rem; font-weight: 700;'>AED {support_amount:,.2f}</div>
            </div>
            <p style='margin: 1rem 0 0 0; color: #047857;'>
                You are eligible for financial assistance and enablement programs.
            </p>
        </div>
        """, unsafe_allow_html=True)
    elif decision == 'SOFT_DECLINED':
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                    padding: 2.5rem; border-radius: 12px; text-align: center; margin: 2rem 0;'>
            <div style='font-size: 5rem; margin-bottom: 1rem;'>⚠️</div>
            <h1 style='margin: 0; color: #92400e;'>Application Under Review</h1>
            <div style='background: white; padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0; display: inline-block;'>
                <div style='color: #6b7280; font-size: 0.875rem;'>Transitional Support Available</div>
                <div style='color: #d97706; font-size: 3rem; font-weight: 700;'>AED {support_amount:,.2f}</div>
            </div>
            <p style='margin: 1rem 0 0 0; color: #92400e;'>
                You qualify for enablement programs and transitional assistance.
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%); 
                    padding: 2.5rem; border-radius: 12px; text-align: center; margin: 2rem 0;'>
            <div style='font-size: 5rem; margin-bottom: 1rem;'>📋</div>
            <h1 style='margin: 0; color: #991b1b;'>Application Not Approved</h1>
            <p style='margin: 1.5rem 0; color: #7f1d1d;'>
                Based on current criteria, you don't qualify for support at this time.
            </p>
            <p style='margin: 0; color: #991b1b; font-size: 0.875rem;'>
                Review the feedback below and consider applying again when circumstances change.
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Detailed tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "✅ Validation",
        "🎓 Programs",
        "💬 AI Chat",
        "📄 Export"
    ])
    
    with tab1:
        show_results_overview(results, support_amount)
    
    with tab2:
        show_validation_results(results)
    
    with tab3:
        show_programs(recommendation)
    
    with tab4:
        show_chatbot(st.session_state.application_id)
    
    with tab5:
        show_export_options(st.session_state.application_id, results)


def show_results_overview(results, support_amount):
    """Show overview tab"""
    st.markdown("### 💰 Financial Overview")
    
    extracted = results.get('extracted_data', {})
    income_data = extracted.get('income_data', {})
    applicant_info = extracted.get('applicant_info', {})
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Monthly Income", f"AED {income_data.get('monthly_income', 0):,.0f}")
    with col2:
        st.metric("Monthly Expenses", f"AED {income_data.get('monthly_expenses', 0):,.0f}")
    with col3:
        eligibility = results.get('eligibility', {})
        score = eligibility.get('eligibility_score', 0)
        st.metric("Eligibility Score", f"{score:.0%}", 
                 delta="Qualified" if score >= 0.6 else "Not Qualified")
    with col4:
        st.metric("Support Amount", f"AED {support_amount:,.0f}",
                 delta=f"AED {support_amount:,.0f}/month")
    
    st.divider()
    
    # Applicant profile
    st.markdown("### 👤 Applicant Profile")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"**Name:** {applicant_info.get('full_name', 'N/A')}")
        st.markdown(f"**Emirates ID:** {applicant_info.get('id_number', 'N/A')}")
    with col2:
        st.markdown(f"**Nationality:** {applicant_info.get('nationality', 'N/A')}")
        st.markdown(f"**Date of Birth:** {applicant_info.get('date_of_birth', 'N/A')}")
    with col3:
        employment = extracted.get('employment_data', {})
        st.markdown(f"**Employment:** {employment.get('employment_status', 'N/A')}")
        st.markdown(f"**Company:** {employment.get('company_name', 'N/A')}")
    
    st.divider()
    
    # Decision reasoning
    st.markdown("### 🧠 AI Decision Reasoning")
    recommendation = results.get('recommendation', {})
    reasoning = recommendation.get('reasoning', 'No reasoning provided')
    
    st.markdown(f"""
    <div style='background: #f9fafb; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3b82f6;'>
        {reasoning}
    </div>
    """, unsafe_allow_html=True)


def show_validation_results(results):
    """Show validation tab"""
    st.markdown("### ✅ Document Validation Report")
    
    validation = results.get('validation', {})
    is_valid = validation.get('is_valid', False)
    issues = validation.get('issues', [])
    
    # Overall status
    if is_valid:
        st.success("✅ All documents validated successfully - No issues found")
    else:
        st.warning(f"⚠️ {len(issues)} validation issue(s) detected")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        completeness = validation.get('completeness_score', 0)
        st.metric("Completeness", f"{completeness:.0%}",
                 delta="Complete" if completeness >= 0.8 else "Incomplete")
    with col2:
        confidence = validation.get('confidence_score', 0)
        st.metric("Confidence", f"{confidence:.0%}",
                 delta="High" if confidence >= 0.8 else "Low")
    with col3:
        st.metric("Documents", f"{len(st.session_state.uploaded_files)}")
    with col4:
        st.metric("Issues", f"{len(issues)}",
                 delta="Clean" if len(issues) == 0 else "Review")
    
    st.divider()
    
    # Issues breakdown
    if issues:
        st.markdown("### 🔍 Issues Detected")
        
        critical = [i for i in issues if i.get('severity') == 'critical']
        warnings = [i for i in issues if i.get('severity') == 'warning']
        infos = [i for i in issues if i.get('severity') == 'info']
        
        if critical:
            st.error(f"🔴 {len(critical)} Critical Issue(s)")
            for issue in critical:
                with st.expander(f"❗ {issue.get('field', 'Unknown')}"):
                    st.write(f"**Message:** {issue.get('message', 'No message')}")
                    if issue.get('suggested_resolution'):
                        st.info(f"💡 **Fix:** {issue['suggested_resolution']}")
        
        if warnings:
            st.warning(f"🟡 {len(warnings)} Warning(s)")
            for issue in warnings:
                with st.expander(f"⚠️ {issue.get('field', 'Unknown')}"):
                    st.write(f"**Message:** {issue.get('message', 'No message')}")
                    if issue.get('suggested_resolution'):
                        st.info(f"💡 **Suggestion:** {issue['suggested_resolution']}")
        
        if infos:
            st.info(f"🔵 {len(infos)} Informational Note(s)")
            for issue in infos:
                with st.expander(f"ℹ️ {issue.get('field', 'Unknown')}"):
                    st.write(f"**Message:** {issue.get('message', 'No message')}")
    else:
        st.success("🎉 No validation issues found! All documents are in perfect order.")


def show_programs(recommendation):
    """Show recommended programs"""
    st.markdown("### 🎓 Recommended Support Programs")
    
    programs = recommendation.get('programs', [])
    
    if programs:
        st.info(f"📋 You qualify for **{len(programs)}** support program(s)")
        
        for idx, program in enumerate(programs, 1):
            priority = program.get('priority', 'medium')
            priority_colors = {
                'high': ('🔴', '#fee2e2', '#991b1b'),
                'medium': ('🟡', '#fef3c7', '#92400e'),
                'low': ('🟢', '#d1fae5', '#065f46')
            }
            icon, bg_color, text_color = priority_colors.get(priority, ('⚪', '#f3f4f6', '#1f2937'))
            
            st.markdown(f"""
            <div style='background: {bg_color}; padding: 1.5rem; border-radius: 8px; margin: 1rem 0;'>
                <div style='display: flex; align-items: center; margin-bottom: 0.5rem;'>
                    <span style='font-size: 1.5rem; margin-right: 0.5rem;'>{icon}</span>
                    <h3 style='margin: 0; color: {text_color};'>{idx}. {program.get('name', 'Program')}</h3>
                </div>
                <p style='color: {text_color}; margin: 0.5rem 0;'><strong>Category:</strong> {program.get('category', 'N/A')}</p>
                <p style='color: {text_color}; margin: 0.5rem 0;'>{program.get('description', 'No description available')}</p>
                <p style='color: {text_color}; margin: 0.5rem 0;'><strong>Duration:</strong> {program.get('duration', 'N/A')}</p>
                {f"<p style='color: {text_color}; margin: 0.5rem 0;'><strong>Benefits:</strong> {program.get('benefits')}</p>" if program.get('benefits') else ""}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No specific programs recommended at this time. Chat with our AI assistant to explore options!")


def show_chatbot(application_id):
    """Show AI chatbot interface"""
    st.markdown("### 🤖 AI Assistant - Ask Anything!")
    
    st.markdown("""
    <div style='background: #eff6ff; padding: 1rem; border-radius: 8px; margin: 1rem 0;'>
        <p style='margin: 0;'>💬 I'm here to help! Ask me about your decision, how to improve, or any questions about the application process.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick action buttons
    st.markdown("#### 🚀 Quick Questions")
    col1, col2, col3 = st.columns(3)
    
    quick_questions = {
        col1: ("💡 Why this decision?", "Explain in detail why I was approved/declined and the key factors."),
        col2: ("📈 How to improve?", "What can I do to improve my chances in future applications?"),
        col3: ("🔍 Key factors", "What were the most important factors in my application evaluation?")
    }
    
    for col, (button_text, question) in quick_questions.items():
        with col:
            if st.button(button_text, use_container_width=True):
                with st.spinner("Thinking..."):
                    response = chat_with_agent(application_id, question)
                    if response:
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": question
                        })
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                        st.rerun()
    
    st.divider()
    
    # Chat history
    if st.session_state.chat_history:
        st.markdown("#### 💬 Conversation History")
        for msg in st.session_state.chat_history[-6:]:  # Show last 6 messages
            if msg['role'] == 'user':
                st.markdown(f"""
                <div style='background: #eff6ff; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; text-align: right;'>
                    <strong>You:</strong> {msg['content']}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background: #f9fafb; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; border-left: 3px solid #3b82f6;'>
                    <strong>🤖 AI:</strong> {msg['content']}
                </div>
                """, unsafe_allow_html=True)
        
        if len(st.session_state.chat_history) > 0:
            if st.button("🗑️ Clear Chat History"):
                st.session_state.chat_history = []
                st.rerun()
    
    # Chat input
    st.markdown("#### ✏️ Ask Your Question")
    user_query = st.text_area(
        "Type your question here:",
        placeholder="E.g., Why was my income considered low? What programs can help me?",
        height=100,
        label_visibility="collapsed"
    )
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📤 Send Question", type="primary", use_container_width=True):
            if user_query and user_query.strip():
                with st.spinner("AI is thinking..."):
                    response = chat_with_agent(application_id, user_query.strip())
                    if response:
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": user_query.strip()
                        })
                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": response
                        })
                        st.rerun()
                    else:
                        st.error("Failed to get response. Please try again.")
            else:
                st.warning("Please enter a question first.")


def show_export_options(application_id, results):
    """Show export options"""
    st.markdown("### 📄 Export & Download Options")
    
    st.markdown("""
    <div style='background: #f9fafb; padding: 1.5rem; border-radius: 8px; border-left: 4px solid #3b82f6;'>
        <h4 style='margin: 0 0 0.5rem 0;'>📥 Available Exports</h4>
        <p style='margin: 0;'>Download your application results and supporting documents for your records.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Results Export")
        if st.button("📥 Download Results (JSON)", use_container_width=True):
            st.download_button(
                label="💾 Save JSON File",
                data=json.dumps(results, indent=2),
                file_name=f"application_{application_id}_results.json",
                mime="application/json",
                use_container_width=True
            )
        
        if st.button("📥 Download Summary (PDF)", use_container_width=True):
            st.info("PDF export feature coming soon!")
    
    with col2:
        st.markdown("#### 💬 Chat History")
        if st.button("📥 Export Chat History", use_container_width=True):
            if st.session_state.chat_history:
                chat_export = json.dumps(st.session_state.chat_history, indent=2)
                st.download_button(
                    label="💾 Save Chat History",
                    data=chat_export,
                    file_name=f"application_{application_id}_chat.json",
                    mime="application/json",
                    use_container_width=True
                )
            else:
                st.warning("No chat history to export yet.")
        
        if st.button("📧 Email Results", use_container_width=True):
            st.info("Email feature coming soon!")


# ========== API Helper Functions ==========

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
        st.error("❌ Cannot connect to API server. Please ensure it's running on port 8000.")
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
    """Get application status"""
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
    """Get application results"""
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
        return "⏱️ The AI is taking longer than expected to respond. This might be due to complex analysis. Please try again or simplify your question."
    except requests.exceptions.RequestException:
        return "❌ Unable to connect to the AI service. Please check your connection and try again."
    except Exception:
        return None
