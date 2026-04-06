import streamlit as st
 
st.set_page_config(
    page_title="Forecastly — Amazon Intelligence",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap');
 
html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
}
 

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #080C14 !important;
    border-right: 1px solid #1C2333;
}
section[data-testid="stSidebar"] * { color: #CDD1DC !important; }
 
/* Sidebar logo block */
.sidebar-logo {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 1.4rem 1rem 1rem 1rem;
    border-bottom: 1px solid #1C2333;
    margin-bottom: 1rem;
}
.sidebar-logo-icon {
    font-size: 1.6rem;
    line-height: 1;
}
.sidebar-logo-text h2 {
    margin: 0 !important;
    font-size: 1.05rem !important;
    font-weight: 800 !important;
    color: #E8EAF0 !important;
    letter-spacing: 1px;
}
.sidebar-logo-text p {
    margin: 0 !important;
    font-size: 0.62rem !important;
    color: #E8452C !important;
    letter-spacing: 2.5px;
    font-weight: 600 !important;
}
 
/* Nav label */
.nav-label {
    font-size: 0.65rem !important;
    letter-spacing: 2px !important;
    color: #4A5568 !important;
    font-weight: 700 !important;
    padding: 0 0.2rem;
    margin-bottom: 0.3rem;
}
 
/* Home button styling — make it look like the active page */
.home-btn > button {
    background: linear-gradient(135deg, #E8452C18, #E8452C08) !important;
    color: #E8EAF0 !important;
    border: 1px solid #E8452C55 !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.9rem !important;
    width: 100% !important;
    text-align: left !important;
    padding: 0.55rem 0.8rem !important;
    margin-bottom: 0.25rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.3px !important;
}
.home-btn > button:hover {
    background: linear-gradient(135deg, #E8452C30, #E8452C14) !important;
    border-color: #E8452C99 !important;
}
 
/* page_link override — match home button style */
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"] {
    display: block !important;
    padding: 0.5rem 0.8rem !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: #9AA3B2 !important;
    text-decoration: none !important;
    border: 1px solid transparent !important;
    margin-bottom: 0.2rem !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebar"] a[data-testid="stPageLink-NavLink"]:hover {
    background: #0F1520 !important;
    border-color: #1C2333 !important;
    color: #E8EAF0 !important;
}
 
/* Main bg */
.main { background: #080C14; }
.block-container { padding-top: 2rem !important; }
 
/* Metric cards */
[data-testid="stMetric"] {
    background: #0F1520;
    border: 1px solid #1C2333;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
}
[data-testid="stMetricValue"] {
    font-family: 'DM Mono', monospace !important;
    font-size: 1.6rem !important;
    color: #E8EAF0 !important;
}
[data-testid="stMetricDelta"] { font-size: 0.8rem !important; }
 
/* Dataframe */
[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
 
/* Primary buttons */
.stButton > button {
    background: #E8452C !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
}
 
/* Headings */
h1, h2, h3 { font-family: 'Syne', sans-serif !important; font-weight: 800 !important; }
 
/* Divider accent */
hr { border-color: #1C2333 !important; }
</style>
""", unsafe_allow_html=True)
 
# ── Sidebar nav ─────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo block (replaces top-left corner header)
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🔥</div>
        <div class="sidebar-logo-text">
            <h2>FORECASTLY</h2>
            <p>AMAZON INTELLIGENCE</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
 

 
    st.divider()
    st.caption("Forecastly v1.0 · Phase 1")
 
# ── Home screen ─────────────────────────────────────────────────────────────
st.markdown("# 🔥 Forecastly")
st.markdown("### Amazon Invoice Intelligence System")
st.markdown("""
Upload your **separate Amazon invoices** (FBA Fees, Shipping, Storage, Advertising, Returns)
and Forecastly merges them into a unified P&L, per-SKU profit breakdown, and sales forecast.
""")
 
col1, col2, col3 = st.columns(3)
col1.info("📤 **Step 1** — Upload each invoice type separately")
col2.info("📊 **Step 2** — View merged P&L and SKU profit")
col3.info("🔮 **Step 3** — See 14-day sales forecast")
