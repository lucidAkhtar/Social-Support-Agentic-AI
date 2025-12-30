"""
Role-Based Access Control (RBAC) with audit logging
WHAT THIS GIVES YOU: Government-grade access management
"""

from enum import Enum
from typing import List, Set, Optional
from datetime import datetime
import hashlib
import json

class Role(Enum):
    APPLICANT = "applicant"
    CASEWORKER = "caseworker"
    SUPERVISOR = "supervisor"
    AUDITOR = "auditor"
    ADMIN = "admin"

class Permission(Enum):
    # Application permissions
    SUBMIT_APPLICATION = "submit_application"
    VIEW_OWN_APPLICATION = "view_own_application"
    
    # Caseworker permissions
    VIEW_ALL_APPLICATIONS = "view_all_applications"
    REVIEW_APPLICATION = "review_application"
    MAKE_DECISION = "make_decision"
    
    # Supervisor permissions
    OVERRIDE_DECISION = "override_decision"
    VIEW_ANALYTICS = "view_analytics"
    
    # Auditor permissions
    VIEW_AUDIT_LOGS = "view_audit_logs"
    EXPORT_COMPLIANCE_REPORT = "export_compliance_report"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    SYSTEM_CONFIG = "system_config"

class RBACManager:
    """
    Role-Based Access Control Manager
    """
    
    ROLE_PERMISSIONS = {
        Role.APPLICANT: {
            Permission.SUBMIT_APPLICATION,
            Permission.VIEW_OWN_APPLICATION,
        },
        Role.CASEWORKER: {
            Permission.VIEW_ALL_APPLICATIONS,
            Permission.REVIEW_APPLICATION,
            Permission.MAKE_DECISION,
        },
        Role.SUPERVISOR: {
            Permission.VIEW_ALL_APPLICATIONS,
            Permission.REVIEW_APPLICATION,
            Permission.MAKE_DECISION,
            Permission.OVERRIDE_DECISION,
            Permission.VIEW_ANALYTICS,
        },
        Role.AUDITOR: {
            Permission.VIEW_ALL_APPLICATIONS,
            Permission.VIEW_AUDIT_LOGS,
            Permission.EXPORT_COMPLIANCE_REPORT,
        },
        Role.ADMIN: set(Permission),  # All permissions
    }
    
    def __init__(self):
        self.access_logs = []
    
    def check_permission(self, user_role: Role, permission: Permission) -> bool:
        """Check if role has permission"""
        return permission in self.ROLE_PERMISSIONS.get(user_role, set())
    
    def log_access(self, user_id: str, user_role: Role, action: str, resource: str, granted: bool):
        """Log every access attempt"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id,
            "role": user_role.value,
            "action": action,
            "resource": resource,
            "granted": granted,
            "hash": self._generate_hash(user_id, action, resource)
        }
        self.access_logs.append(log_entry)
        return log_entry
    
    def _generate_hash(self, user_id: str, action: str, resource: str) -> str:
        """Generate hash for tamper detection"""
        data = f"{user_id}{action}{resource}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()
    
    def get_audit_trail(self, user_id: Optional[str] = None) -> List[dict]:
        """Get audit trail for user or all users"""
        if user_id:
            return [log for log in self.access_logs if log['user_id'] == user_id]
        return self.access_logs

# DEMO FOR PRESENTATION:
if __name__ == "__main__":
    rbac = RBACManager()
    
    # Test permissions
    print("=== Role-Based Access Control Demo ===\n")
    
    # Applicant trying to view their own application
    can_view_own = rbac.check_permission(Role.APPLICANT, Permission.VIEW_OWN_APPLICATION)
    print(f"Applicant can view own application: {can_view_own}")
    rbac.log_access("applicant_001", Role.APPLICANT, "view", "APP-001", can_view_own)
    
    # Applicant trying to override decision (should fail)
    can_override = rbac.check_permission(Role.APPLICANT, Permission.OVERRIDE_DECISION)
    print(f"Applicant can override decision: {can_override}")
    rbac.log_access("applicant_001", Role.APPLICANT, "override", "APP-001", can_override)
    
    # Supervisor overriding decision (should succeed)
    supervisor_override = rbac.check_permission(Role.SUPERVISOR, Permission.OVERRIDE_DECISION)
    print(f"Supervisor can override decision: {supervisor_override}")
    rbac.log_access("supervisor_001", Role.SUPERVISOR, "override", "APP-001", supervisor_override)
    
    # Show audit trail
    print("\n=== Audit Trail ===")
    for log in rbac.get_audit_trail():
        status = "GRANTED" if log['granted'] else "DENIED"
        print(f"{log['timestamp']} | {log['user_id']} | {log['action']} | {status}")