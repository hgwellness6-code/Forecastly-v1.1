import streamlit as st

st.set_page_config(
    page_title="Forecastly — Amazon Intelligence",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Define pages using st.Page (required for newer Streamlit) ────────────────
pg_home      = st.Page("pages/1_overview.py",  title="Home",            icon="🏠", default=True)
pg_upload    = st.Page("pages/2_Upload.py",     title="Upload Invoices", icon="📤")
pg_dashboard = st.Page("pages/3_Dashboard.py", title="Dashboard",       icon="📊")
pg_forecast  = st.Page("pages/4_Forecast.py",  title="Forecast",        icon="🔮")

# Register all pages with navigation hidden (we draw our own sidebar nav)
pg = st.navigation(
    [pg_home, pg_upload, pg_dashboard, pg_forecast],
    position="hidden",
)

# ── Global CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Syne', sans-serif !important;
}

/* ── Hide Streamlit's built-in top nav & sidebar header ── */
[data-testid="stSidebarHeader"],
[data-testid="stSidebarNav"],
section[data-testid="stSidebar"] ul,
nav[data-testid="stSidebarNav"] {
    display: none !important;
}
/* Remove top padding left by hidden header */
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
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
    # Logo block
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-logo-icon">🔥</div>
        <div class="sidebar-logo-text">
            <h2>FORECASTLY</h2>
            <p>AMAZON INTELLIGENCE</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<p class="nav-label">NAVIGATION</p>', unsafe_allow_html=True)

    # Use st.Page objects — this is the fix for the KeyError crash
    st.page_link(pg_home,      label="🏠  Home",             use_container_width=True)
    st.page_link(pg_upload,    label="📤  Upload Invoices",  use_container_width=True)
    st.page_link(pg_dashboard, label="📊  Dashboard",        use_container_width=True)
    st.page_link(pg_forecast,  label="🔮  Forecast",         use_container_width=True)

    st.divider()
    st.caption("Forecastly v1.1 · Phase 1")

# ── Run the selected page ────────────────────────────────────────────────────
pg.run()
