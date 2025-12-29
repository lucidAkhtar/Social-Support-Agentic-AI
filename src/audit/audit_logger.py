"""
Immutable Audit Logging System
WHAT THIS GIVES YOU: Complete accountability and compliance
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
import sqlite3

class AuditLogger:
    """
    Blockchain-style audit logging
    Each entry is linked to previous entry via hash chain
    """
    
    def __init__(self, db_path: str = "data/audit.db"):
        self.db_path = db_path
        Path("data").mkdir(exist_ok=True)
        self._init_db()
        self.previous_hash = self._get_last_hash()
    
    def _init_db(self):
        """Initialize audit database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor TEXT NOT NULL,
                action TEXT NOT NULL,
                resource TEXT NOT NULL,
                details TEXT,
                previous_hash TEXT,
                current_hash TEXT NOT NULL,
                UNIQUE(current_hash)
            )
        """)
        conn.commit()
        conn.close()
    
    def log_event(
        self,
        event_type: str,
        actor: str,
        action: str,
        resource: str,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Log an event with blockchain-style hash linking
        Returns: Hash of this entry
        """
        timestamp = datetime.utcnow().isoformat()
        details_json = json.dumps(details) if details else "{}"
        
        # Create hash chain
        entry_data = f"{timestamp}{event_type}{actor}{action}{resource}{details_json}{self.previous_hash}"
        current_hash = hashlib.sha256(entry_data.encode()).hexdigest()
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        conn.execute(
            """INSERT INTO audit_log 
               (timestamp, event_type, actor, action, resource, details, previous_hash, current_hash)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (timestamp, event_type, actor, action, resource, details_json, self.previous_hash, current_hash)
        )
        conn.commit()
        conn.close()
        
        # Update chain
        self.previous_hash = current_hash
        
        return current_hash
    
    def _get_last_hash(self) -> str:
        """Get hash of last entry"""
        conn = sqlite3.connect(self.db_path)
        result = conn.execute(
            "SELECT current_hash FROM audit_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        conn.close()
        
        return result[0] if result else "GENESIS"
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify audit log hasn't been tampered with
        CRITICAL FOR GOVERNMENT: Prove logs are authentic
        """
        conn = sqlite3.connect(self.db_path)
        entries = conn.execute(
            "SELECT timestamp, event_type, actor, action, resource, details, previous_hash, current_hash FROM audit_log ORDER BY id"
        ).fetchall()
        conn.close()
        
        if not entries:
            return {"valid": True, "total_entries": 0}
        
        previous_hash = "GENESIS"
        for i, entry in enumerate(entries):
            timestamp, event_type, actor, action, resource, details, stored_prev_hash, stored_curr_hash = entry
            
            # Recalculate hash
            entry_data = f"{timestamp}{event_type}{actor}{action}{resource}{details}{previous_hash}"
            calculated_hash = hashlib.sha256(entry_data.encode()).hexdigest()
            
            # Verify
            if calculated_hash != stored_curr_hash:
                return {
                    "valid": False,
                    "tampered_entry": i + 1,
                    "message": "Audit log has been tampered with!"
                }
            
            if stored_prev_hash != previous_hash:
                return {
                    "valid": False,
                    "broken_chain": i + 1,
                    "message": "Hash chain broken!"
                }
            
            previous_hash = stored_curr_hash
        
        return {
            "valid": True,
            "total_entries": len(entries),
            "last_hash": previous_hash,
            "message": "Audit log integrity verified ✓"
        }
    
    def get_audit_trail(
        self,
        actor: Optional[str] = None,
        resource: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query audit logs with filters"""
        query = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        
        if actor:
            query += " AND actor = ?"
            params.append(actor)
        if resource:
            query += " AND resource = ?"
            params.append(resource)
        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)
        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        results = conn.execute(query, params).fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def export_compliance_report(self, output_path: str = "audit_report.json"):
        """
        Export compliance report for regulators
        """
        integrity_check = self.verify_integrity()
        all_logs = self.get_audit_trail()
        
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "integrity_verification": integrity_check,
            "total_events": len(all_logs),
            "audit_logs": all_logs,
            "statistics": {
                "unique_actors": len(set(log['actor'] for log in all_logs)),
                "event_types": len(set(log['event_type'] for log in all_logs)),
            }
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report

# DEMO FOR PRESENTATION:
if __name__ == "__main__":
    audit = AuditLogger()
    
    print("=== Audit Logging Demo ===\n")
    
    # Log some events
    print("Logging events...")
    audit.log_event(
        "APPLICATION_SUBMITTED",
        "applicant_001",
        "submit",
        "APP-20241230-001",
        {"name": "Ahmed", "income": 12000}
    )
    
    audit.log_event(
        "DECISION_MADE",
        "ai_agent_decision",
        "approve",
        "APP-20241230-001",
        {"decision": "approved", "confidence": 0.92}
    )
    
    audit.log_event(
        "DATA_ACCESSED",
        "caseworker_005",
        "view",
        "APP-20241230-001",
        {"reason": "manual review"}
    )
    
    # Verify integrity
    print("\nVerifying audit log integrity...")
    result = audit.verify_integrity()
    print(json.dumps(result, indent=2))
    
    # Export compliance report
    print("\nExporting compliance report...")
    report = audit.export_compliance_report()
    print(f"Report exported with {report['total_events']} events")