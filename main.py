import os
import sqlite3
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from engine.agent import sentinel_agent, DB_PATH

app = FastAPI(
    title="Supply Chain Sentinel API",
    description="REST API for Autonomous Supply Chain Risk Monitoring & Mitigation",
    version="1.0.0"
)

# Request / Response Schemas
class NewsScanRequest(BaseModel):
    title: str
    link: Optional[str] = "https://news.google.com"
    published: Optional[str] = "Today"

class OrderItem(BaseModel):
    order_id: int
    item_name: str
    quantity: int
    supplier_name: str
    expected_delivery: str

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
    # Verify SQLite DB connection
    if not os.path.exists(DB_PATH):
        raise HTTPException(status_code=500, detail="Database file not found.")
    
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
    """
    Triggers the autonomous LangGraph Sentinel Agent against an incoming news article.
    Returns threat assessment, impacted active orders, and executive alert.
    """
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
        # Run agent workflow
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