import streamlit as st
import requests
import os

# Page Configuration
st.set_page_config(
    page_title="Supply Chain Sentinel",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ Autonomous Supply Chain Sentinel")
st.caption("AI-Powered Real-Time Supply Chain Risk Detection & Mitigation Engine")

# Sidebar - API Endpoint Configuration
st.sidebar.header("⚙️ Configuration")
api_base_url = st.sidebar.text_input(
    "FastAPI Service URL",
    value=os.getenv("SENTINEL_API_URL", "https://supply-chain-sentinel-hz8y.onrender.com")
)

st.sidebar.markdown("---")
st.sidebar.subheader("📌 System Health Check")
if st.sidebar.button("Check API Status"):
    try:
        res = requests.get(f"{api_base_url}/api/health", timeout=5)
        if res.status_code == 200:
            st.sidebar.success(f"Online | Active Orders: {res.json().get('active_orders_tracked')}")
        else:
            st.sidebar.error("API returned error status.")
    except Exception as e:
        st.sidebar.error(f"Cannot reach API: {e}")

# Main Layout - Inputs
st.subheader("📰 Input News Disruptions")

preset_option = st.selectbox(
    "Choose a preset scenario or select Custom:",
    [
        "Custom Input",
        "Taiwan Typhoon (Port Delays - Taiwan)",
        "German Port Strike (Logistics Halt - Germany)",
        "Nominal Tech Industry News (No Disruptions)"
    ]
)

if preset_option == "Taiwan Typhoon (Port Delays - Taiwan)":
    default_title = "Typhoon damages major port infrastructure in Taiwan, delaying all cargo exports"
elif preset_option == "German Port Strike (Logistics Halt - Germany)":
    default_title = "Logistics union announces multi-day strike across major German ports and railways"
elif preset_option == "Nominal Tech Industry News (No Disruptions)":
    default_title = "Global Tech Summit announces annual schedule for hardware keynotes"
else:
    default_title = ""

headline = st.text_area("News Headline / RSS Article Title", value=default_title, height=100)

if st.button("🚀 Trigger Autonomous Risk Scan", type="primary"):
    if not headline.strip():
        st.warning("Please enter a news headline to analyze.")
    else:
        with st.spinner("Sentinel Agent assessing risk, cross-referencing inventory, and formulating mitigation strategies..."):
            try:
                payload = {"title": headline, "link": "https://news.google.com", "published": "Today"}
                response = requests.post(f"{api_base_url}/api/scan", json=payload, timeout=25)
                
                if response.status_code == 200:
                    data = response.json()
                    st.success("Scan Completed!")
                    
                    # Risk Banner Metrics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Threat Detected", "YES ⚠️" if data["is_threat"] else "NO ✅")
                    with col2:
                        st.metric("Affected Region", data["affected_country"])
                    with col3:
                        st.metric("Impacted Active Orders", data["impacted_orders_count"])
                    
                    st.markdown("---")
                    
                    # Results Sections
                    if data["is_threat"]:
                        st.subheader("📦 Impacted Orders in Transit")
                        if data["affected_orders"]:
                            st.table(data["affected_orders"])
                        else:
                            st.info("No active shipments currently bound from or routed through this region.")
                        
                        st.subheader("🚨 Executive Mitigation Alert")
                        st.markdown(data["final_alert"])
                    else:
                        st.info("No operational supply chain threats identified for this news event.")
                else:
                    st.error(f"API Error ({response.status_code}): {response.text}")
            except Exception as e:
                st.error(f"Failed to communicate with Sentinel API: {e}")