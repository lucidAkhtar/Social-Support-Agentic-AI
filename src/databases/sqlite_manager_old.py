"""
SQLite Manager for structured relational data.
Stores applications, profiles, decisions, and validation results.
"""

import sqlite3
import json
from typing import Optional, Dict, List, Any
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SQLiteManager:
    """Manages structured relational data in SQLite."""
    
    def __init__(self, db_path: str = "data/databases/social_support.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn: Optional[sqlite3.Connection] = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create all required tables."""
        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        
        # Applications table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                application_id TEXT PRIMARY KEY,
                applicant_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'pending',
                current_stage TEXT DEFAULT 'not_started'
            )
        """)
        
        # Applicant profiles table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS applicant_profiles (
                application_id TEXT PRIMARY KEY,
                id_number TEXT,
                monthly_income REAL,
                monthly_expenses REAL,
                employment_status TEXT,
                years_experience INTEGER,
                total_assets REAL,
                total_liabilities REAL,
                net_worth REAL,
                credit_score INTEGER,
                family_size INTEGER,
                has_disabilities INTEGER DEFAULT 0,
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # Documents table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                application_id TEXT NOT NULL,
                document_type TEXT NOT NULL,
                file_path TEXT,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed INTEGER DEFAULT 0,
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # Validation results table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS validation_results (
                validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT NOT NULL,
                is_valid INTEGER NOT NULL,
                completeness_score REAL,
                confidence_score REAL,
                issues_json TEXT,
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # Eligibility decisions table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS eligibility_decisions (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT NOT NULL,
                is_eligible INTEGER NOT NULL,
                eligibility_score REAL,
                ml_prediction_score REAL,
                policy_rules_score REAL,
                need_score REAL,
                final_decision TEXT,
                reasons_json TEXT,
                decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # Recommendations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT NOT NULL,
                decision_type TEXT NOT NULL,
                support_amount REAL,
                programs_json TEXT,
                reasoning TEXT,
                recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # Audit log table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT,
                agent_name TEXT NOT NULL,
                action TEXT NOT NULL,
                details_json TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        self.conn.commit()
        logger.info(f"SQLite database initialized at {self.db_path}")
    
    def create_application(self, application_id: str, applicant_name: str) -> bool:
        """Create a new application record."""
        try:
            self.conn.execute(
                "INSERT INTO applications (application_id, applicant_name) VALUES (?, ?)",
                (application_id, applicant_name)
            )
            self.conn.commit()
            self.log_action(application_id, "System", "application_created", 
                          {"applicant_name": applicant_name})
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Application {application_id} already exists")
            return False
    
    def update_application_stage(self, application_id: str, stage: str):
        """Update the processing stage of an application."""
        self.conn.execute(
            "UPDATE applications SET current_stage = ?, updated_at = ? WHERE application_id = ?",
            (stage, datetime.now(), application_id)
        )
        self.conn.commit()
    
    def save_applicant_profile(self, application_id: str, profile_data: Dict[str, Any]):
        """Save or update applicant profile data."""
        fields = [
            "id_number", "monthly_income", "monthly_expenses", "employment_status",
            "years_experience", "total_assets", "total_liabilities", "net_worth",
            "credit_score", "family_size", "has_disabilities"
        ]
        
        values = [application_id] + [profile_data.get(f) for f in fields]
        
        self.conn.execute(f"""
            INSERT OR REPLACE INTO applicant_profiles 
            (application_id, {', '.join(fields)})
            VALUES (?, {', '.join(['?'] * len(fields))})
        """, values)
        self.conn.commit()
        self.log_action(application_id, "ExtractionAgent", "profile_saved", profile_data)
    
    def add_document(self, application_id: str, document_id: str, 
                    document_type: str, file_path: str):
        """Add a document record."""
        self.conn.execute("""
            INSERT INTO documents (document_id, application_id, document_type, file_path)
            VALUES (?, ?, ?, ?)
        """, (document_id, application_id, document_type, file_path))
        self.conn.commit()
    
    def save_validation_result(self, application_id: str, validation_data: Dict[str, Any]):
        """Save validation results."""
        issues = validation_data.get("issues", [])
        issues_json = json.dumps(issues)
        
        # Count issue severities
        critical = len([i for i in issues if i.get("severity") == "critical"])
        warnings = len([i for i in issues if i.get("severity") == "warning"])
        info = len([i for i in issues if i.get("severity") == "info"])
        
        self.conn.execute("""
            INSERT INTO validation_results 
            (application_id, is_valid, data_completeness_score, confidence_score, 
             critical_issues, warnings, info_notices, issues_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            application_id,
            int(validation_data.get("is_valid", False)),
            validation_data.get("completeness_score", 0.0),
            validation_data.get("confidence_score", 0.0),
            critical,
            warnings,
            info,
            issues_json
        ))
        self.conn.commit()
        self.log_action(application_id, "ValidationAgent", "validation_completed", validation_data)
    
    def save_eligibility_decision(self, application_id: str, decision_data: Dict[str, Any]):
        """Save eligibility decision."""
        reasons_json = json.dumps(decision_data.get("reasons", []))
        self.conn.execute("""
            INSERT INTO eligibility_decisions
            (application_id, is_eligible, eligibility_score, ml_prediction_score,
             policy_rules_score, need_score, final_decision, reasons_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            application_id,
            int(decision_data.get("is_eligible", False)),
            decision_data.get("eligibility_score", 0.0),
            decision_data.get("ml_prediction_score", 0.0),
            decision_data.get("policy_rules_score", 0.0),
            decision_data.get("need_score", 0.0),
            decision_data.get("final_decision", "DECLINED"),
            reasons_json
        ))
        self.conn.commit()
        self.log_action(application_id, "EligibilityAgent", "decision_made", decision_data)
    
    def save_recommendation(self, application_id: str, recommendation_data: Dict[str, Any]):
        """Save recommendation."""
        programs_json = json.dumps(recommendation_data.get("programs", []))
        self.conn.execute("""
            INSERT INTO recommendations
            (application_id, decision_type, financial_support_amount, financial_support_type, programs_json, reasoning)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            application_id,
            recommendation_data.get("decision_type", "DECLINED"),
            recommendation_data.get("financial_support_amount", 0.0),
            recommendation_data.get("financial_support_type", ""),
            programs_json,
            recommendation_data.get("reasoning", "")
        ))
        self.conn.commit()
        self.log_action(application_id, "RecommendationAgent", "recommendation_generated", 
                       recommendation_data)
    
    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get application details."""
        cursor = self.conn.execute(
            "SELECT * FROM applications WHERE application_id = ?",
            (application_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_applicant_profile(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get applicant profile."""
        cursor = self.conn.execute(
            "SELECT * FROM applicant_profiles WHERE application_id = ?",
            (application_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_validation_history(self, application_id: str) -> List[Dict[str, Any]]:
        """Get all validation results for an application."""
        cursor = self.conn.execute(
            "SELECT * FROM validation_results WHERE application_id = ? ORDER BY validated_at DESC",
            (application_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_decision_history(self, application_id: str) -> List[Dict[str, Any]]:
        """Get all decisions for an application."""
        cursor = self.conn.execute(
            "SELECT * FROM eligibility_decisions WHERE application_id = ? ORDER BY decided_at DESC",
            (application_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def get_audit_trail(self, application_id: str) -> List[Dict[str, Any]]:
        """Get complete audit trail for an application."""
        cursor = self.conn.execute(
            "SELECT * FROM audit_log WHERE application_id = ? ORDER BY timestamp ASC",
            (application_id,)
        )
        return [dict(row) for row in cursor.fetchall()]
    
    def log_action(self, application_id: str, agent_name: str, 
                   action: str, details: Dict[str, Any]):
        """Log an action to audit trail."""
        details_json = json.dumps(details, default=str)
        self.conn.execute("""
            INSERT INTO audit_log (application_id, agent_name, action, details_json)
            VALUES (?, ?, ?, ?)
        """, (application_id, agent_name, action, details_json))
        self.conn.commit()
    
    def search_applications(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search applications with filters."""
        query = "SELECT * FROM applications WHERE 1=1"
        params = []
        
        if "status" in filters:
            query += " AND status = ?"
            params.append(filters["status"])
        
        if "current_stage" in filters:
            query += " AND current_stage = ?"
            params.append(filters["current_stage"])
        
        query += " ORDER BY created_at DESC"
        
        cursor = self.conn.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get overall system statistics."""
        cursor = self.conn.execute("""
            SELECT 
                COUNT(*) as total_applications,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending
            FROM applications
        """)
        app_stats = dict(cursor.fetchone())
        
        cursor = self.conn.execute("""
            SELECT 
                final_decision,
                COUNT(*) as count
            FROM eligibility_decisions
            GROUP BY final_decision
        """)
        decision_stats = {row["final_decision"]: row["count"] for row in cursor.fetchall()}
        
        return {
            "applications": app_stats,
            "decisions": decision_stats
        }
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("SQLite connection closed")
