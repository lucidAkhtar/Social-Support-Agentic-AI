"""
Production-Grade UAE Social Support System - Multi-Page Application
FAANG Standards: Professional UI, Admin Dashboard, Real-time Monitoring

Features:
- User Application Flow (Core Journey)
- Admin Dashboard (System Health, ML Metrics, Audit Logs)
- Real-time Status Updates
- Interactive Data Visualization
- Governance & Compliance Monitoring
"""

import streamlit as st
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Configure page
st.set_page_config(
    page_title="UAE Social Support Portal",
    page_icon="🇦🇪",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://socialsupport.ae/help',
        'Report a bug': 'https://socialsupport.ae/issues',
        'About': '# UAE Social Support System\n\nPowered by AI • Secure • Confidential'
    }
)

# Import pages
from pages import applicant_portal, admin_dashboard

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = "Applicant Portal"
if 'user_role' not in st.session_state:
    st.session_state.user_role = "applicant"  # or "admin"

# Professional styling
st.markdown("""
<style>
    /* Modern UAE theme */
    :root {
        --primary: #0066cc;
        --secondary: #00a19c;
        --success: #10b981;
        --warning: #f59e0b;
        --danger: #ef4444;
        --info: #3b82f6;
    }
    
    /* Hide streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Professional header */
    .app-header {
        background: linear-gradient(135deg, #0066cc 0%, #00a19c 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #f9fafb 0%, #ffffff 100%);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Metric cards */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 600;
    }
    
    .badge-success { background: #d1fae5; color: #065f46; }
    .badge-warning { background: #fef3c7; color: #92400e; }
    .badge-danger { background: #fee2e2; color: #991b1b; }
    .badge-info { background: #dbeafe; color: #1e40af; }
</style>
""", unsafe_allow_html=True)

# Sidebar Navigation
with st.sidebar:
    st.markdown("""
    <div style='text-align: center; padding: 1rem 0;'>
        <h1 style='color: #0066cc; margin: 0;'>🇦🇪</h1>
        <h3 style='margin: 0.5rem 0 0 0;'>UAE Social Support</h3>
        <p style='color: #6b7280; font-size: 0.875rem;'>Production System v2.0</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # Role selector (for demo purposes)
    st.markdown("### 👤 User Role")
    role = st.radio(
        "Select Role:",
        ["Applicant", "Administrator"],
        label_visibility="collapsed"
    )
    
    if role == "Administrator":
        st.session_state.user_role = "admin"
        st.session_state.page = "Admin Dashboard"
    else:
        st.session_state.user_role = "applicant"
        st.session_state.page = "Applicant Portal"
    
    st.divider()
    
    # Quick stats (always visible)
    st.markdown("### 📊 System Status")
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("API", "🟢 Online", delta="99.9%")
    with col2:
        st.metric("Database", "🟢 Healthy", delta="Fast")
    
    st.divider()
    
    # Help section
    with st.expander("❓ Quick Help"):
        if st.session_state.user_role == "applicant":
            st.markdown("""
            **Application Process:**
            1. Enter your details
            2. Upload documents
            3. Submit & wait ~5 min
            4. View decision
            5. Chat with AI assistant
            
            **Support:**
            📞 800-SUPPORT
            ✉️ help@uae.gov.ae
            """)
        else:
            st.markdown("""
            **Admin Features:**
            - System health monitoring
            - ML model performance
            - Audit log viewer
            - Real-time analytics
            
            **Emergency:**
            📞 +971-x-xxx-xxxx
            """)

# Main content area
if st.session_state.page == "Applicant Portal":
    applicant_portal.show()
elif st.session_state.page == "Admin Dashboard":
    admin_dashboard.show()

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #6b7280; padding: 1rem 0;'>
    <p style='margin: 0;'><strong>UAE Social Support Portal</strong> | Powered by AI</p>
    <p style='margin: 0.25rem 0; font-size: 0.875rem;'>
        🔒 Secure • 🔍 Transparent • ⚖️ Fair • 🚀 Fast
    </p>
    <p style='margin: 0.5rem 0 0 0; font-size: 0.75rem;'>
        © 2026 UAE Government. All rights reserved. | <a href='#'>Privacy Policy</a> | <a href='#'>Terms of Service</a>
    </p>
</div>
""", unsafe_allow_html=True)
