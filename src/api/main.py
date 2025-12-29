from fastapi import FastAPI, UploadFile, File, Form
from pydantic import BaseModel
import json
import sqlite3
from datetime import datetime
from src.database.sqlite_client import DatabaseClient

app = FastAPI(title="Social Support AI")
db = DatabaseClient()

class ApplicationData(BaseModel):
    name: str
    emirates_id: str
    phone: str
    email: str
    monthly_income: float
    family_size: int
    employment_status: str

@app.post("/api/v1/applications/submit")
async def submit_application(
    data: str = Form(...),
    emirates_id: UploadFile = File(None),
    bank_statement: UploadFile = File(None),
    resume: UploadFile = File(None),
    assets: UploadFile = File(None)
):
    # Parse form data
    app_data = json.loads(data)
    app_id = f"APP-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # Store in database
    conn = sqlite3.connect(db.db_path)
    conn.execute(
        "INSERT INTO applications (id, applicant_name, emirates_id, status, data) VALUES (?, ?, ?, ?, ?)",
        (app_id, app_data['name'], app_data['emirates_id'], 'submitted', json.dumps(app_data))
    )
    conn.commit()
    conn.close()
    
    return {"application_id": app_id, "status": "submitted"}

@app.get("/api/v1/applications/{app_id}")
async def get_application(app_id: str):
    conn = sqlite3.connect(db.db_path)
    result = conn.execute(
        "SELECT * FROM applications WHERE id = ?", (app_id,)
    ).fetchone()
    conn.close()
    
    if result:
        return {
            "id": result[0],
            "name": result[1],
            "status": result[4]
        }
    return {"error": "Not found"}

@app.get("/health")
async def health():
    return {"status": "healthy", "model": "mistral"}