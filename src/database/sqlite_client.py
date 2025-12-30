"""
SQLite client with comprehensive schema for social support applications.
Handles relational data + JSON documents (JSON1 extension).
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any


class SQLiteClient:
    """SQLite database client with full schema for application processing."""

    def __init__(self, db_path: str = "data/databases/social_support.db"):
        """Initialize SQLite client and create schema if needed."""
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.conn = None
        self._initialize_connection()
        self._create_schema()

    def _initialize_connection(self):
        """Create database connection with JSON1 enabled."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        # Enable JSON1 extension
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA foreign_keys=ON")

    def _create_schema(self):
        """Create all necessary tables for application processing."""
        cursor = self.conn.cursor()

        # ===== CORE TABLES =====
        
        # Applications
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                app_id TEXT PRIMARY KEY,
                applicant_id TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'SUBMITTED',
                submission_date TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Applicants
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applicants (
                applicant_id TEXT PRIMARY KEY,
                full_name TEXT NOT NULL,
                emirates_id TEXT UNIQUE,
                date_of_birth TEXT,
                age INTEGER,
                email TEXT,
                phone TEXT,
                marital_status TEXT,
                family_size INTEGER,
                dependents INTEGER,
                education_level TEXT
            )
        """)

        # Employment
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employment (
                employment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT NOT NULL,
                employer TEXT,
                position TEXT,
                start_date TEXT,
                end_date TEXT,
                years_employed REAL,
                monthly_salary REAL,
                employment_status TEXT,
                FOREIGN KEY(applicant_id) REFERENCES applicants(applicant_id)
            )
        """)

        # Income (multiple sources)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS income (
                income_id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT NOT NULL,
                source_type TEXT,
                amount REAL NOT NULL,
                frequency TEXT,
                verified INTEGER DEFAULT 0,
                verified_date TEXT,
                FOREIGN KEY(applicant_id) REFERENCES applicants(applicant_id)
            )
        """)

        # Family members
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS family_members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT NOT NULL,
                name TEXT,
                relationship TEXT,
                age INTEGER,
                dependency_status TEXT,
                FOREIGN KEY(applicant_id) REFERENCES applicants(applicant_id)
            )
        """)

        # Assets
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT NOT NULL,
                asset_type TEXT,
                description TEXT,
                value REAL,
                acquisition_date TEXT,
                FOREIGN KEY(applicant_id) REFERENCES applicants(applicant_id)
            )
        """)

        # Liabilities
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS liabilities (
                liability_id INTEGER PRIMARY KEY AUTOINCREMENT,
                applicant_id TEXT NOT NULL,
                liability_type TEXT,
                amount REAL,
                creditor TEXT,
                monthly_payment REAL,
                FOREIGN KEY(applicant_id) REFERENCES applicants(applicant_id)
            )
        """)

        # Documents
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT NOT NULL,
                document_type TEXT,
                file_path TEXT,
                upload_date TEXT,
                processing_status TEXT DEFAULT 'PENDING',
                FOREIGN KEY(app_id) REFERENCES applications(app_id)
            )
        """)

        # Extraction Results (with JSON data)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_results (
                extraction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT NOT NULL,
                extracted_data JSON,
                confidence_score REAL,
                extraction_date TEXT,
                FOREIGN KEY(app_id) REFERENCES applications(app_id)
            )
        """)

        # Validation Results
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS validation_results (
                validation_id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT NOT NULL,
                quality_score REAL,
                consistency_score REAL,
                completeness_score REAL,
                validation_date TEXT,
                passed INTEGER DEFAULT 0,
                FOREIGN KEY(app_id) REFERENCES applications(app_id)
            )
        """)

        # Decisions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS decisions (
                decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT NOT NULL,
                decision_type TEXT,
                decision_score REAL,
                ml_confidence REAL,
                business_rule_score REAL,
                rationale TEXT,
                decision_date TEXT,
                recommended_actions JSON,
                FOREIGN KEY(app_id) REFERENCES applications(app_id)
            )
        """)

        # Audit Log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                app_id TEXT,
                action TEXT,
                action_date TEXT,
                details JSON,
                FOREIGN KEY(app_id) REFERENCES applications(app_id)
            )
        """)

        # Create indices for performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applicants_email ON applicants(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_employment_applicant ON employment(applicant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_income_applicant ON income(applicant_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_app ON documents(app_id)")

        self.conn.commit()

    def insert_application(self, app_data: Dict) -> str:
        """Insert application and applicant data."""
        cursor = self.conn.cursor()
        
        app_id = app_data.get("application_id", app_data.get("app_id"))
        
        # Insert application
        cursor.execute("""
            INSERT OR REPLACE INTO applications (app_id, applicant_id, status, submission_date)
            VALUES (?, ?, ?, ?)
        """, (
            app_id,
            app_id.replace("APP-", "APPLICANT-"),
            "SUBMITTED",
            app_data.get("submission_date", datetime.now().isoformat())
        ))

        # Insert applicant
        applicant_id = app_id.replace("APP-", "APPLICANT-")
        cursor.execute("""
            INSERT OR REPLACE INTO applicants 
            (applicant_id, full_name, emirates_id, date_of_birth, age, email, phone, 
             marital_status, family_size, dependents, education_level)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            applicant_id,
            app_data.get("full_name"),
            app_data.get("emirates_id"),
            app_data.get("date_of_birth"),
            app_data.get("age"),
            app_data.get("email"),
            app_data.get("phone"),
            app_data.get("marital_status"),
            app_data.get("family_size"),
            app_data.get("dependents"),
            app_data.get("education_level")
        ))

        # Insert employment
        if app_data.get("employer"):
            cursor.execute("""
                INSERT INTO employment 
                (applicant_id, employer, position, years_employed, monthly_salary, employment_status)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                applicant_id,
                app_data.get("employer"),
                app_data.get("position"),
                app_data.get("years_employed"),
                app_data.get("monthly_income"),
                app_data.get("employment_status")
            ))

        # Insert income
        if app_data.get("monthly_income"):
            cursor.execute("""
                INSERT INTO income (applicant_id, source_type, amount, frequency, verified)
                VALUES (?, ?, ?, ?, ?)
            """, (
                applicant_id,
                "Primary Employment",
                app_data.get("monthly_income"),
                "Monthly",
                1
            ))

        # Insert assets
        total_assets = app_data.get("total_assets", 0)
        if total_assets > 0:
            cursor.execute("""
                INSERT INTO assets (applicant_id, asset_type, description, value)
                VALUES (?, ?, ?, ?)
            """, (
                applicant_id,
                "Overall",
                "Total assets",
                total_assets
            ))

        # Insert liabilities
        total_liabilities = app_data.get("total_liabilities", 0)
        if total_liabilities > 0:
            cursor.execute("""
                INSERT INTO liabilities (applicant_id, liability_type, amount)
                VALUES (?, ?, ?)
            """, (
                applicant_id,
                "Overall",
                total_liabilities
            ))

        self.conn.commit()
        return app_id

    def insert_extraction_result(self, app_id: str, extracted_data: Dict, confidence: float):
        """Insert extraction results."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO extraction_results (app_id, extracted_data, confidence_score, extraction_date)
            VALUES (?, json(?), ?, ?)
        """, (
            app_id,
            json.dumps(extracted_data),
            confidence,
            datetime.now().isoformat()
        ))
        self.conn.commit()

    def insert_validation_result(self, app_id: str, quality: float, consistency: float, completeness: float):
        """Insert validation results."""
        cursor = self.conn.cursor()
        passed = 1 if quality >= 0.75 else 0
        cursor.execute("""
            INSERT INTO validation_results 
            (app_id, quality_score, consistency_score, completeness_score, validation_date, passed)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            app_id,
            quality,
            consistency,
            completeness,
            datetime.now().isoformat(),
            passed
        ))
        self.conn.commit()

    def insert_decision(self, app_id: str, decision_type: str, decision_score: float, 
                       ml_confidence: float, business_score: float, rationale: str, actions: List):
        """Insert decision."""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO decisions 
            (app_id, decision_type, decision_score, ml_confidence, business_rule_score, 
             rationale, decision_date, recommended_actions)
            VALUES (?, ?, ?, ?, ?, ?, ?, json(?))
        """, (
            app_id,
            decision_type,
            decision_score,
            ml_confidence,
            business_score,
            rationale,
            datetime.now().isoformat(),
            json.dumps(actions)
        ))
        self.conn.commit()

    def get_application(self, app_id: str) -> Optional[Dict]:
        """Get application and all related data."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE app_id = ?", (app_id,))
        return dict(cursor.fetchone()) if cursor.fetchone() else None

    def get_applicant_profile(self, applicant_id: str) -> Dict:
        """Get complete applicant profile."""
        cursor = self.conn.cursor()
        
        # Get applicant
        cursor.execute("SELECT * FROM applicants WHERE applicant_id = ?", (applicant_id,))
        result = dict(cursor.fetchone()) if cursor.fetchone() else {}
        
        # Get employment
        cursor.execute("SELECT * FROM employment WHERE applicant_id = ?", (applicant_id,))
        result["employment"] = [dict(row) for row in cursor.fetchall()]
        
        # Get income
        cursor.execute("SELECT * FROM income WHERE applicant_id = ?", (applicant_id,))
        result["income"] = [dict(row) for row in cursor.fetchall()]
        
        # Get assets
        cursor.execute("SELECT * FROM assets WHERE applicant_id = ?", (applicant_id,))
        result["assets"] = [dict(row) for row in cursor.fetchall()]
        
        # Get liabilities
        cursor.execute("SELECT * FROM liabilities WHERE applicant_id = ?", (applicant_id,))
        result["liabilities"] = [dict(row) for row in cursor.fetchall()]
        
        return result

    def get_statistics(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM applications")
        total_apps = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM applicants")
        total_applicants = cursor.fetchone()[0]
        
        cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        status_breakdown = {row[0]: row[1] for row in cursor.fetchall()}
        
        cursor.execute("SELECT AVG(amount) FROM income")
        avg_income = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM decisions WHERE decision_type = 'APPROVE'")
        total_approvals = cursor.fetchone()[0]
        
        return {
            "total_applications": total_apps,
            "total_applicants": total_applicants,
            "status_breakdown": status_breakdown,
            "average_income": avg_income,
            "total_approvals": total_approvals
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Backward compatibility
DatabaseClient = SQLiteClient