"""
Modules for UAE Social Support Portal
Contains reusable view components called by main_app.py
Note: Folder named 'modules' instead of 'pages' to avoid Streamlit's automatic page detection
"""

from . import applicant_portal
from . import admin_dashboard

__all__ = ['applicant_portal', 'admin_dashboard']
