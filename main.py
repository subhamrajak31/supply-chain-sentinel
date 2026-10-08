import os
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from engine.agent import sentinel_agent, DB_PATH

app = FastAPI(
    title="Supply Chain Sentinel API",
    description="REST API for Autonomous Supply Chain Risk Monitoring & Mitigation",
    version="1.0.0"
)

def init_sqlite_db():
    """Ensures SQLite database, directory, and tables exist with seed data on startup."""
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS active_orders (
            order_id INTEGER PRIMARY KEY,
            item_name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            supplier_name TEXT NOT NULL,
            origin_country TEXT NOT NULL,
            expected_delivery TEXT NOT NULL
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM active_orders")
    if cursor.fetchone()[0] == 0:
        seed_data = [
            (101, "Microcontroller Board A1", 5000, "Taiwan Semi Co", "Taiwan", "2026-10-15"),
            (102, "Precision Steel Bearings", 12000, "RheinMetall Precision", "Germany", "2026-10-20"),
            (103, "Lithium Battery Cells", 800, "Tokyo Battery Corp", "Japan", "2026-11-01")
        ]
        cursor.executemany('''
            INSERT INTO active_orders (order_id, item_name, quantity, supplier_name, origin_country, expected_delivery)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', seed_data)
        conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    init_sqlite_db()

# Request / Response Schemas
class NewsScanRequest(BaseModel):
    title: str
    link: Optional[str] = "https://news.google.com"
    published: Optional[str] = "Today"

class ScanResultResponse(BaseModel):
    news_title: str
    is_threat: bool
    affected_country: str
    risk_summary: str
    impacted_orders_count: int
    affected_orders: List[Dict[str, Any]]
    final_alert: str

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Supply Chain Sentinel API",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    init_sqlite_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM active_orders")
    active_orders_count = cursor.fetchone()[0]
    conn.close()

    return {
        "status": "healthy",
        "database": "connected",
        "active_orders_tracked": active_orders_count
    }

@app.post("/api/scan", response_model=ScanResultResponse)
def trigger_supply_chain_scan(payload: NewsScanRequest):
    init_sqlite_db()
    initial_state = {
        "news_article": {
            "title": payload.title,
            "link": payload.link,
            "published": payload.published
        },
        "is_threat": False,
        "affected_country": "None",
        "risk_summary": "",
        "affected_orders": [],
        "final_alert": ""
    }

    try:
        output = sentinel_agent.invoke(initial_state)

        return ScanResultResponse(
            news_title=payload.title,
            is_threat=output.get("is_threat", False),
            affected_country=output.get("affected_country", "None"),
            risk_summary=output.get("risk_summary", ""),
            impacted_orders_count=len(output.get("affected_orders", [])),
            affected_orders=output.get("affected_orders", []),
            final_alert=output.get("final_alert", "Operations nominal. No threat detected.")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")