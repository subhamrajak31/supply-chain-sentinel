# 🛡️ Autonomous Supply Chain Sentinel

An autonomous, production-grade supply chain risk mitigation engine built with **LangGraph**, **Gemini 1.5**, **FastAPI**, **SQLite**, and **Streamlit**, live-deployed on **Render**.

---

## 🏗️ Tech Stack & Architecture

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Orchestrator** | LangGraph | State machine managing cyclical agent workflow |
| **LLM Brain** | Gemini 1.5 Flash | Threat detection, entity extraction, and mitigation strategy |
| **Database** | SQLite3 | Relational ledger for orders, inventory, and supplier contacts |
| **REST API** | FastAPI / Uvicorn | Async web service exposing operational endpoints |
| **Frontend UI** | Streamlit | Executive dashboard for manual scans & real-time monitoring |
| **Deployment** | Render / GitHub CI | Production web hosting with automated deployment pipelines |

---

## 🔄 System Workflow

```text
[ RSS News Feed / User Headline ]
              │
              ▼
    [ LangGraph Agent ]
              │
              ├──► 1. Risk Evaluator Node (Gemini 1.5)
              │       └── Classifies event threat & identifies target region
              │
              ├──► 2. SQL Query Engine Node
              │       └── Queries active_orders, inventory, & suppliers tables
              │
              └──► 3. Executive Synthesizer Node (Gemini 1.5)
                      └── Formulates action alerts & rerouting strategies
              │
              ▼
 [ FastAPI Endpoint / Streamlit UI ]