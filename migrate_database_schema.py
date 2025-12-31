"""
Database Migration Script - Add New Extraction Fields
Safely adds columns to the applications table for newly extracted fields
"""
import sqlite3
from pathlib import Path

DB_PATH = Path("data/databases/applications.db")

def migrate():
    """Add new columns to applications table"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # List of new columns to add
    new_columns = [
        ("company_name", "TEXT"),
        ("current_position", "TEXT"),
        ("join_date", "TEXT"),
        ("credit_rating", "TEXT"),
        ("credit_accounts", "TEXT"),  # JSON array of credit accounts
        ("payment_ratio", "REAL"),
        ("total_outstanding", "REAL"),
        ("work_experience_years", "INTEGER"),
        ("education_level", "TEXT"),
    ]
    
    print(f"🔧 Migrating database schema at: {DB_PATH}")
    
    for column_name, column_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE applications ADD COLUMN {column_name} {column_type}")
            print(f"  ✅ Added column: {column_name} ({column_type})")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"  ⏭️  Column {column_name} already exists, skipping")
            else:
                print(f"  ❌ Error adding {column_name}: {e}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Database migration complete!")

if __name__ == "__main__":
    migrate()
