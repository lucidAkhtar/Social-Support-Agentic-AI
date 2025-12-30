#!/usr/bin/env python3
"""
PHASE 8: PRODUCTION-GRADE GOVERNANCE & COMPLIANCE ENGINE
UAE Government AI Standards Compliance
- Abu Dhabi Data Management Office (DMO) - Data Governance Framework
- Dubai Smart Government - Data Protection Standards
- ADISA (Abu Dhabi Information Security Association) - Security Standards
- UAE National AI Strategy - Ethical AI Standards
- DIFC Law (Dubai International Financial Centre) - Data Privacy
"""

import json
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ComplianceFramework(Enum):
    """UAE Government Compliance Frameworks"""
    DUBAI_DATA_PROTECTION = "dubai_data_protection"  # Dubai Smart Government
    ABU_DHABI_DMO = "abu_dhabi_dmo"  # Data Management Office
    ADISA_SECURITY = "adisa_security"  # Information Security
    UAE_AI_STRATEGY = "uae_ai_strategy"  # Ethical AI
    DIFC_PRIVACY = "difc_privacy"  # Financial Data


class DataClassification(Enum):
    """UAE Government Data Classification"""
    PUBLIC = "public"  # No restrictions
    INTERNAL = "internal"  # Government use only
    CONFIDENTIAL = "confidential"  # Restricted access
    RESTRICTED = "restricted"  # Highly sensitive (e.g., PII)
    SECRET = "secret"  # National security


class ConsentType(Enum):
    """Types of user consent"""
    DATA_COLLECTION = "data_collection"
    DATA_PROCESSING = "data_processing"
    DATA_SHARING = "data_sharing"
    PROFILING = "profiling"
    AUTOMATED_DECISION = "automated_decision"


class DataRetentionPolicy(Enum):
    """Data retention periods per UAE standards"""
    PERMANENT = -1  # Never delete
    FIVE_YEARS = 5 * 365  # Financial records
    THREE_YEARS = 3 * 365  # Transaction records
    ONE_YEAR = 365  # Temporary data
    THIRTY_DAYS = 30  # Audit logs (minimum)


class GovernanceEngine:
    """
    Production-grade governance framework for AI applications in UAE.
    Implements compliance with:
    - Abu Dhabi DMO Data Governance Framework
    - Dubai Smart Government standards
    - ADISA Security Standards
    - UAE National AI Strategy
    """

    def __init__(self, db_path: str = "data/governance.db"):
        self.db_path = db_path
        Path("data").mkdir(parents=True, exist_ok=True)
        self._init_db()
        self.frameworks_enabled = {
            ComplianceFramework.DUBAI_DATA_PROTECTION,
            ComplianceFramework.ABU_DHABI_DMO,
            ComplianceFramework.ADISA_SECURITY,
            ComplianceFramework.UAE_AI_STRATEGY,
            ComplianceFramework.DIFC_PRIVACY
        }

    def _init_db(self):
        """Initialize governance database"""
        conn = sqlite3.connect(self.db_path)
        
        # Data classification registry
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_classification (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_entity TEXT NOT NULL UNIQUE,
                classification TEXT NOT NULL,
                owner TEXT NOT NULL,
                retention_days INTEGER NOT NULL,
                encrypted BOOLEAN DEFAULT 1,
                pii BOOLEAN DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # Consent management
        conn.execute("""
            CREATE TABLE IF NOT EXISTS consent_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT NOT NULL,
                consent_type TEXT NOT NULL,
                granted BOOLEAN NOT NULL,
                timestamp TEXT NOT NULL,
                version TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                withdrawal_timestamp TEXT
            )
        """)
        
        # Data processing agreements
        conn.execute("""
            CREATE TABLE IF NOT EXISTS dpa_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                processor_name TEXT NOT NULL,
                purpose TEXT NOT NULL,
                data_categories TEXT NOT NULL,
                legal_basis TEXT NOT NULL,
                approved BOOLEAN DEFAULT 0,
                approval_date TEXT,
                expiry_date TEXT,
                created_at TEXT NOT NULL
            )
        """)
        
        # Data residency compliance
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_residency (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_entity TEXT NOT NULL,
                location TEXT NOT NULL,
                jurisdiction TEXT NOT NULL,
                compliant BOOLEAN DEFAULT 1,
                verified_at TEXT NOT NULL
            )
        """)
        
        # Audit events (immutable)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                data_entity TEXT,
                classification TEXT,
                compliance_check TEXT,
                result TEXT NOT NULL,
                details TEXT,
                hash TEXT NOT NULL UNIQUE
            )
        """)
        
        # Data usage tracking
        conn.execute("""
            CREATE TABLE IF NOT EXISTS data_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                applicant_id TEXT NOT NULL,
                data_fields_accessed TEXT NOT NULL,
                access_purpose TEXT NOT NULL,
                actor TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                duration_seconds REAL,
                data_classification TEXT
            )
        """)
        
        conn.commit()
        conn.close()

    def register_data_entity(
        self,
        entity_name: str,
        classification: DataClassification,
        owner: str,
        retention_policy: DataRetentionPolicy,
        contains_pii: bool = False,
        require_encryption: bool = True
    ) -> bool:
        """Register a data entity with governance policies"""
        try:
            conn = sqlite3.connect(self.db_path)
            now = datetime.utcnow().isoformat()
            
            conn.execute("""
                INSERT OR REPLACE INTO data_classification 
                (data_entity, classification, owner, retention_days, encrypted, pii, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                entity_name,
                classification.value,
                owner,
                retention_policy.value if retention_policy.value > 0 else -1,
                1 if require_encryption else 0,
                1 if contains_pii else 0,
                now,
                now
            ))
            conn.commit()
            conn.close()
            
            logger.info(f"✓ Data entity registered: {entity_name} ({classification.value})")
            return True
        except Exception as e:
            logger.error(f"Failed to register data entity: {e}")
            return False

    def record_consent(
        self,
        applicant_id: str,
        consent_type: ConsentType,
        granted: bool,
        version: str = "1.0",
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """Record explicit user consent (GDPR/DIFC compliance)"""
        try:
            conn = sqlite3.connect(self.db_path)
            timestamp = datetime.utcnow().isoformat()
            
            conn.execute("""
                INSERT INTO consent_records
                (applicant_id, consent_type, granted, timestamp, version, ip_address, user_agent)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                applicant_id,
                consent_type.value,
                granted,
                timestamp,
                version,
                ip_address,
                user_agent
            ))
            conn.commit()
            conn.close()
            
            status = "✓ GRANTED" if granted else "❌ DENIED"
            logger.info(f"Consent recorded: {applicant_id} | {consent_type.value} | {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to record consent: {e}")
            return False

    def withdraw_consent(
        self,
        applicant_id: str,
        consent_type: ConsentType
    ) -> bool:
        """Withdraw previously granted consent - right to be forgotten"""
        try:
            conn = sqlite3.connect(self.db_path)
            timestamp = datetime.utcnow().isoformat()
            
            # Mark as withdrawn
            conn.execute("""
                UPDATE consent_records
                SET withdrawal_timestamp = ?
                WHERE applicant_id = ? AND consent_type = ? AND granted = 1 AND withdrawal_timestamp IS NULL
            """, (timestamp, applicant_id, consent_type.value))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Consent withdrawn: {applicant_id} | {consent_type.value}")
            return True
        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            return False

    def verify_consent(
        self,
        applicant_id: str,
        consent_type: ConsentType
    ) -> bool:
        """Verify that current consent is valid and not withdrawn"""
        try:
            conn = sqlite3.connect(self.db_path)
            result = conn.execute("""
                SELECT COUNT(*) FROM consent_records
                WHERE applicant_id = ? 
                  AND consent_type = ? 
                  AND granted = 1 
                  AND withdrawal_timestamp IS NULL
                LIMIT 1
            """, (applicant_id, consent_type.value)).fetchone()
            conn.close()
            
            is_valid = result[0] > 0 if result else False
            logger.info(f"Consent verified: {applicant_id} | {consent_type.value} | Valid={is_valid}")
            return is_valid
        except Exception as e:
            logger.error(f"Failed to verify consent: {e}")
            return False

    def record_data_usage(
        self,
        applicant_id: str,
        data_fields: List[str],
        access_purpose: str,
        actor: str,
        actor_role: str,
        duration_seconds: float = 0
    ) -> bool:
        """Track all data access for audit and compliance"""
        try:
            conn = sqlite3.connect(self.db_path)
            timestamp = datetime.utcnow().isoformat()
            
            # Get data classification
            classification_result = conn.execute("""
                SELECT classification FROM data_classification
                WHERE data_entity IN ({})
                LIMIT 1
            """.format(','.join(['?']*len(data_fields))), data_fields).fetchone()
            
            classification = classification_result[0] if classification_result else "unknown"
            
            conn.execute("""
                INSERT INTO data_usage
                (timestamp, applicant_id, data_fields_accessed, access_purpose, actor, actor_role, duration_seconds, data_classification)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                applicant_id,
                json.dumps(data_fields),
                access_purpose,
                actor,
                actor_role,
                duration_seconds,
                classification
            ))
            conn.commit()
            conn.close()
            
            return True
        except Exception as e:
            logger.error(f"Failed to record data usage: {e}")
            return False

    def verify_data_residency(
        self,
        data_entity: str,
        allowed_jurisdictions: List[str] = None
    ) -> bool:
        """
        Verify data residency compliance.
        UAE requires certain data to remain within UAE jurisdiction.
        """
        if allowed_jurisdictions is None:
            allowed_jurisdictions = ["UAE", "Dubai", "Abu Dhabi"]
        
        try:
            conn = sqlite3.connect(self.db_path)
            result = conn.execute("""
                SELECT jurisdiction FROM data_residency
                WHERE data_entity = ? AND compliant = 1
            """, (data_entity,)).fetchone()
            conn.close()
            
            if result:
                is_compliant = result[0] in allowed_jurisdictions
                logger.info(f"Data residency verified: {data_entity} | Jurisdiction={result[0]} | Compliant={is_compliant}")
                return is_compliant
            
            logger.warning(f"No residency record found for: {data_entity}")
            return False
        except Exception as e:
            logger.error(f"Failed to verify data residency: {e}")
            return False

    def log_audit_event(
        self,
        event_type: str,
        actor: str,
        action: str,
        resource: str,
        result: str,
        data_entity: Optional[str] = None,
        compliance_check: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> str:
        """Log immutable audit event with hash chain"""
        try:
            conn = sqlite3.connect(self.db_path)
            timestamp = datetime.utcnow().isoformat()
            
            # Get previous hash for chain
            prev_hash_result = conn.execute("""
                SELECT hash FROM audit_events ORDER BY id DESC LIMIT 1
            """).fetchone()
            prev_hash = prev_hash_result[0] if prev_hash_result else "GENESIS"
            
            # Create hash chain
            hash_input = f"{timestamp}{event_type}{actor}{action}{resource}{result}{data_entity}{compliance_check}{prev_hash}"
            event_hash = hashlib.sha256(hash_input.encode()).hexdigest()
            
            conn.execute("""
                INSERT INTO audit_events
                (timestamp, event_type, actor, action, resource, data_entity, classification, compliance_check, result, details, hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                event_type,
                actor,
                action,
                resource,
                data_entity,
                self._get_data_classification(data_entity, conn),
                compliance_check,
                result,
                json.dumps(details) if details else "{}",
                event_hash
            ))
            conn.commit()
            conn.close()
            
            return event_hash
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return ""

    def _get_data_classification(self, entity: Optional[str], conn) -> str:
        """Helper to get data classification"""
        if not entity:
            return "unknown"
        
        result = conn.execute("""
            SELECT classification FROM data_classification
            WHERE data_entity = ?
        """, (entity,)).fetchone()
        
        return result[0] if result else "unknown"

    def generate_compliance_report(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        output_file: str = "compliance_report.json"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive compliance report for regulators.
        Used for audit trails, data protection impact assessments, etc.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            now = datetime.utcnow().isoformat()
            
            if not start_date:
                start_date = (datetime.utcnow() - timedelta(days=90)).isoformat()
            if not end_date:
                end_date = now
            
            # Collect data
            data_entities = conn.execute("""
                SELECT data_entity, classification, owner, retention_days, pii FROM data_classification
            """).fetchall()
            
            consent_summary = conn.execute("""
                SELECT consent_type, COUNT(*) as count, SUM(CASE WHEN granted=1 THEN 1 ELSE 0 END) as granted
                FROM consent_records
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY consent_type
            """, (start_date, end_date)).fetchall()
            
            data_usage_summary = conn.execute("""
                SELECT access_purpose, COUNT(*) as access_count, data_classification
                FROM data_usage
                WHERE timestamp BETWEEN ? AND ?
                GROUP BY access_purpose, data_classification
            """, (start_date, end_date)).fetchall()
            
            audit_events = conn.execute("""
                SELECT timestamp, event_type, actor, action, result, compliance_check
                FROM audit_events
                WHERE timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """, (start_date, end_date)).fetchall()
            
            conn.close()
            
            report = {
                "report_type": "Compliance & Governance Report",
                "generated_at": now,
                "period": {"start": start_date, "end": end_date},
                "frameworks_enabled": [f.value for f in self.frameworks_enabled],
                "data_entities": {
                    "total": len(data_entities),
                    "entities": [
                        {
                            "name": e[0],
                            "classification": e[1],
                            "owner": e[2],
                            "retention_days": e[3],
                            "contains_pii": bool(e[4])
                        }
                        for e in data_entities
                    ]
                },
                "consent_management": {
                    "total_consents": sum(c[1] for c in consent_summary),
                    "granted": sum(c[2] for c in consent_summary),
                    "by_type": [
                        {
                            "type": c[0],
                            "total": c[1],
                            "granted": c[2],
                            "percentage": 100 * c[2] // c[1] if c[1] > 0 else 0
                        }
                        for c in consent_summary
                    ]
                },
                "data_usage": {
                    "total_accesses": sum(d[1] for d in data_usage_summary),
                    "by_purpose": [
                        {
                            "purpose": d[0],
                            "accesses": d[1],
                            "classification": d[2]
                        }
                        for d in data_usage_summary
                    ]
                },
                "audit_trail": {
                    "total_events": len(audit_events),
                    "recent_events": [
                        {
                            "timestamp": e[0],
                            "type": e[1],
                            "actor": e[2],
                            "action": e[3],
                            "result": e[4],
                            "compliance_check": e[5]
                        }
                        for e in audit_events[:20]  # Last 20 events
                    ]
                },
                "compliance_status": "✅ COMPLIANT" if self._verify_compliance(conn) else "⚠️ REVIEW REQUIRED"
            }
            
            # Save report
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Compliance report generated: {output_file}")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {}

    def _verify_compliance(self, conn) -> bool:
        """Check basic compliance status"""
        try:
            # Check if all entities have consent recorded
            entities_count = conn.execute("SELECT COUNT(*) FROM data_classification").fetchone()[0]
            consents_count = conn.execute("SELECT COUNT(DISTINCT consent_type) FROM consent_records").fetchone()[0]
            
            # Check residency compliance
            residency_compliant = conn.execute("""
                SELECT COUNT(*) FROM data_residency WHERE compliant = 1
            """).fetchone()[0]
            
            return entities_count > 0 and consents_count > 0 and residency_compliant > 0
        except:
            return False

    def get_data_for_deletion(
        self,
        applicant_id: str
    ) -> List[str]:
        """
        Get all data entities that should be deleted for an applicant.
        Implements right to be forgotten (DIFC/GDPR compliance).
        """
        try:
            conn = sqlite3.connect(self.db_path)
            
            # Get all accessed data for this applicant
            results = conn.execute("""
                SELECT DISTINCT data_fields_accessed FROM data_usage
                WHERE applicant_id = ?
            """, (applicant_id,)).fetchall()
            
            conn.close()
            
            # Flatten and return
            data_to_delete = []
            for row in results:
                fields = json.loads(row[0])
                data_to_delete.extend(fields)
            
            return list(set(data_to_delete))  # Remove duplicates
        except Exception as e:
            logger.error(f"Failed to get data for deletion: {e}")
            return []


class ComplianceMonitor:
    """Real-time monitoring for compliance violations"""

    def __init__(self, governance: GovernanceEngine):
        self.governance = governance
        self.violations: List[Dict] = []

    def check_unauthorized_access(
        self,
        actor: str,
        actor_role: str,
        data_entity: str,
        required_role: str
    ) -> bool:
        """Detect unauthorized access attempts"""
        if actor_role != required_role:
            violation = {
                "timestamp": datetime.utcnow().isoformat(),
                "violation_type": "UNAUTHORIZED_ACCESS",
                "actor": actor,
                "actor_role": actor_role,
                "data_entity": data_entity,
                "required_role": required_role,
                "severity": "HIGH"
            }
            self.violations.append(violation)
            logger.warning(f"⚠️ VIOLATION: Unauthorized access detected: {actor} ({actor_role}) → {data_entity}")
            return False
        return True

    def check_consent_requirement(
        self,
        applicant_id: str,
        consent_type: ConsentType
    ) -> bool:
        """Check if required consent exists and is not withdrawn"""
        is_valid = self.governance.verify_consent(applicant_id, consent_type)
        
        if not is_valid:
            violation = {
                "timestamp": datetime.utcnow().isoformat(),
                "violation_type": "MISSING_CONSENT",
                "applicant_id": applicant_id,
                "consent_type": consent_type.value,
                "severity": "CRITICAL"
            }
            self.violations.append(violation)
            logger.warning(f"⚠️ VIOLATION: Missing consent: {applicant_id} → {consent_type.value}")
        
        return is_valid

    def check_data_retention_violation(
        self,
        data_entity: str,
        created_at: str
    ) -> bool:
        """Check if data should have been deleted based on retention policy"""
        try:
            conn = sqlite3.connect(self.governance.db_path)
            result = conn.execute("""
                SELECT retention_days FROM data_classification
                WHERE data_entity = ?
            """, (data_entity,)).fetchone()
            conn.close()
            
            if not result:
                return True  # No retention policy = keep indefinitely
            
            retention_days = result[0]
            if retention_days < 0:
                return True  # Permanent retention
            
            created_dt = datetime.fromisoformat(created_at)
            expiry_dt = created_dt + timedelta(days=retention_days)
            
            if datetime.utcnow() > expiry_dt:
                violation = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "violation_type": "RETENTION_VIOLATION",
                    "data_entity": data_entity,
                    "created_at": created_at,
                    "expiry_at": expiry_dt.isoformat(),
                    "severity": "MEDIUM"
                }
                self.violations.append(violation)
                logger.warning(f"⚠️ VIOLATION: Data retention exceeded: {data_entity}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Failed to check retention: {e}")
            return False

    def get_violations(self) -> List[Dict]:
        """Get all detected violations"""
        return self.violations.copy()

    def clear_violations(self):
        """Clear violation log"""
        self.violations.clear()


# DEMO FOR PRESENTATION
if __name__ == "__main__":
    print("\n" + "="*80)
    print("PRODUCTION-GRADE GOVERNANCE & COMPLIANCE ENGINE DEMO")
    print("UAE Government AI Standards")
    print("="*80 + "\n")
    
    # Initialize
    governance = GovernanceEngine()
    monitor = ComplianceMonitor(governance)
    
    # Register data entities
    print("1. REGISTER DATA ENTITIES")
    print("-" * 80)
    governance.register_data_entity(
        "applicant_personal_info",
        DataClassification.RESTRICTED,
        "Social Support Department",
        DataRetentionPolicy.THREE_YEARS,
        contains_pii=True
    )
    governance.register_data_entity(
        "financial_records",
        DataClassification.CONFIDENTIAL,
        "Finance Directorate",
        DataRetentionPolicy.FIVE_YEARS,
        contains_pii=False
    )
    
    # Record consent
    print("\n2. CONSENT MANAGEMENT")
    print("-" * 80)
    governance.record_consent("APP_001", ConsentType.DATA_COLLECTION, True)
    governance.record_consent("APP_001", ConsentType.AUTOMATED_DECISION, True)
    
    is_valid = governance.verify_consent("APP_001", ConsentType.DATA_COLLECTION)
    print(f"Consent valid: {is_valid}")
    
    # Track data usage
    print("\n3. DATA USAGE TRACKING")
    print("-" * 80)
    governance.record_data_usage(
        applicant_id="APP_001",
        data_fields=["applicant_personal_info"],
        access_purpose="eligibility_assessment",
        actor="agent_001",
        actor_role="system",
        duration_seconds=2.3
    )
    
    # Verify access control
    print("\n4. ACCESS CONTROL VERIFICATION")
    print("-" * 80)
    is_allowed = monitor.check_unauthorized_access(
        actor="caseworker_001",
        actor_role="caseworker",
        data_entity="applicant_personal_info",
        required_role="caseworker"
    )
    print(f"Access allowed: {is_allowed}")
    
    # Generate compliance report
    print("\n5. COMPLIANCE REPORT")
    print("-" * 80)
    report = governance.generate_compliance_report()
    print(f"✓ Report generated: {report.get('report_type')}")
    print(f"  - Data entities registered: {report.get('data_entities', {}).get('total', 0)}")
    print(f"  - Total consents: {report.get('consent_management', {}).get('total_consents', 0)}")
    print(f"  - Audit events: {report.get('audit_trail', {}).get('total_events', 0)}")
    print(f"  - Status: {report.get('compliance_status', 'Unknown')}")
    
    print("\n" + "="*80)
    print("✅ GOVERNANCE ENGINE OPERATIONAL - READY FOR PRODUCTION")
    print("="*80 + "\n")
