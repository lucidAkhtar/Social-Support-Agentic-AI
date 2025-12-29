import sqlite3
from pathlib import Path

class DatabaseClient:
    def __init__(self, db_path: str = "data/social_support.db"):
        Path("data").mkdir(exist_ok=True)
        self.db_path = db_path
        self.init_schema()
    
    def init_schema(self):
        conn = sqlite3.connect(self.db_path)
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                applicant_name TEXT,
                emirates_id TEXT,
                submission_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT,
                data TEXT
            );
            
            CREATE TABLE IF NOT EXISTS decisions (
                id TEXT PRIMARY KEY,
                application_id TEXT,
                decision TEXT,
                confidence REAL,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (application_id) REFERENCES applications(id)
            );
        """)
        conn.commit()
        conn.close()