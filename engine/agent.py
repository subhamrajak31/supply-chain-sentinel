import os
import json
import sqlite3
import time
from typing import TypedDict, List, Dict, Any
from dotenv import load_dotenv
from google import genai
from langgraph.graph import StateGraph, END

# 1. Load Environment Variables
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY not found in .env file.")

client = genai.Client(api_key=api_key)
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "inventory_sentinel.db")

# 2. Define State Schema
class SentinelState(TypedDict):
    news_article: Dict[str, Any]
    is_threat: bool
    affected_country: str
    risk_summary: str
    affected_orders: List[Dict[str, Any]]
    final_alert: str

# Helper function with simple retry logic for API calls
def call_gemini_safe(prompt: str, retries: int = 3) -> str:
    """
    Simple wrapper that calls Gemini with automatic retries on server busy errors.
    Uses 'gemini-1.5-flash' for maximum free tier stability.
    """
    for attempt in range(retries):
        try:
            # Using stable gemini-1.5-flash model
            response = client.models.generate_content(
                model="gemini-3.8-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            print(f"⚠️ API attempt {attempt + 1} failed ({e}). Retrying in 2 seconds...")
            time.sleep(2)
            
    raise Exception("Gemini API failed after multiple retries.")

# ---------------------------------------------------------
# Node 1: News Risk Assessor
# ---------------------------------------------------------
def assess_news_risk(state: SentinelState) -> Dict[str, Any]:
    article = state["news_article"]
    title = article.get("title", "")
    
    prompt = f"""
    You are a supply chain risk analyst.
    Analyze this news headline: "{title}"

    Is this a supply chain threat (like a port delay, weather disruption, or strike)?

    Respond strictly in raw JSON format (no markdown code blocks, no backticks):
    {{"is_threat": true, "affected_country": "Taiwan", "risk_summary": "Typhoon damaged port infrastructure"}}

    If not a threat or no country mentioned, return:
    {{"is_threat": false, "affected_country": "None", "risk_summary": "No disruption found"}}
    """

    try:
        raw_response = call_gemini_safe(prompt)
        
        # Clean up Markdown formatting if the model adds ```json ... ```
        cleaned_response = raw_response.replace("```json", "").replace("```", "").strip()
        result = json.loads(cleaned_response)
        
        print(f"🧠 [Agent Assessor] Threat: {result.get('is_threat')} | Country: {result.get('affected_country')}")
        
        return {
            "is_threat": bool(result.get("is_threat", False)),
            "affected_country": str(result.get("affected_country", "None")),
            "risk_summary": str(result.get("risk_summary", ""))
        }
    except Exception as e:
        print(f"❌ LLM Assessment Error: {e}")
        return {"is_threat": False, "affected_country": "None", "risk_summary": "Error evaluating news"}

# ---------------------------------------------------------
# Node 2: Database Inspector (SQLite)
# ---------------------------------------------------------
def check_database_inventory(state: SentinelState) -> Dict[str, Any]:
    country = state["affected_country"]
    print(f"🔍 [Agent DB Inspector] Checking SQLite for active shipments from '{country}'...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Query active shipments matching origin country
    query = """
    SELECT a.order_id, i.item_name, a.quantity, s.name, a.expected_delivery
    FROM active_orders a
    JOIN inventory i ON a.item_id = i.item_id
    JOIN suppliers s ON a.supplier_id = s.supplier_id
    WHERE LOWER(a.origin_country) LIKE LOWER(?) OR LOWER(s.location_country) LIKE LOWER(?)
    """
    
    cursor.execute(query, (f"%{country}%", f"%{country}%"))
    rows = cursor.fetchall()
    conn.close()
    
    affected = []
    for row in rows:
        affected.append({
            "order_id": row[0],
            "item_name": row[1],
            "quantity": row[2],
            "supplier_name": row[3],
            "expected_delivery": row[4]
        })
        
    print(f"📦 [Agent DB Inspector] Found {len(affected)} impacted order(s).")
    return {"affected_orders": affected}

# ---------------------------------------------------------
# Node 3: Mitigation Strategist
# ---------------------------------------------------------
def generate_mitigation_alert(state: SentinelState) -> Dict[str, Any]:
    prompt = f"""
    You are an Operations Manager. A supply chain disruption was detected.

    Disruption Summary: {state['risk_summary']}
    Affected Region: {state['affected_country']}
    Affected Orders in Transit: {json.dumps(state['affected_orders'])}

    Write a brief executive alert containing:
    1. Threat Level (HIGH / CRITICAL)
    2. Summary of Impacted Orders
    3. Recommended Immediate Action
    """

    try:
        alert_text = call_gemini_safe(prompt)
        return {"final_alert": alert_text}
    except Exception as e:
        return {"final_alert": f"Failed to generate alert text: {e}"}

# ---------------------------------------------------------
# Routing Edge Logic
# ---------------------------------------------------------
def route_after_assessment(state: SentinelState) -> str:
    if state["is_threat"] and state["affected_country"] != "None":
        return "check_database"
    return END

# ---------------------------------------------------------
# Build LangGraph Workflow
# ---------------------------------------------------------
workflow = StateGraph(SentinelState)

workflow.add_node("assess_news", assess_news_risk)
workflow.add_node("check_database", check_database_inventory)
workflow.add_node("generate_alert", generate_mitigation_alert)

workflow.set_entry_point("assess_news")

workflow.add_conditional_edges(
    "assess_news",
    route_after_assessment,
    {
        "check_database": "check_database",
        END: END
    }
)

workflow.add_edge("check_database", "generate_alert")
workflow.add_edge("generate_alert", END)

sentinel_agent = workflow.compile()


if __name__ == "__main__":
    # Test news headline targeting Taiwan shipment from database
    sample_news = {
        "title": "Typhoon damages major port infrastructure in Taiwan, delaying all cargo exports",
        "link": "https://news.google.com/rss/articles/123",
        "published": "Sun, 04 Oct 2026 10:00:00 GMT"
    }

    print("🚀 Initializing Autonomous Supply Chain Sentinel Agent...\n")
    
    initial_state = {
        "news_article": sample_news,
        "is_threat": False,
        "affected_country": "None",
        "risk_summary": "",
        "affected_orders": [],
        "final_alert": ""
    }

    final_output = sentinel_agent.invoke(initial_state)

    print("\n" + "="*50)
    print("🚨 FINAL SENTINEL EXECUTIVE ALERT 🚨")
    print("="*50)
    print(final_output.get("final_alert", "Operations nominal."))
