import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.store import get_summary, INVOICE_TYPES
from utils.profit_calc import get_totals

st.markdown("# 🏠 Overview")
st.markdown("Current status of all uploaded invoices and overall P&L.")

# ── Upload status cards ──────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric("Revenue", "₹1,20,000")
col2.metric("Orders", "320")
col3.metric("Profit", "₹45,000")
col4.metric("Expenses", "₹75,000")
st.subheader("📂 Last Uploaded File")

if "df" in st.session_state:
    st.write("Rows:", len(st.session_state["df"]))
else:
    st.warning("No data uploaded yet")

    col1, col2, col3 = st.columns(3)

col1.page_link("pages/2_Upload.py", label="📤 Upload Data", use_container_width=True)
col2.page_link("pages/3_Dashboard.py", label="📊 Dashboard", use_container_width=True)
col3.page_link("pages/4_Forecast.py", label="📈 Forecast", use_container_width=True)


st.markdown("### 📁 Invoice Upload Status")

summary = get_summary()
cols = st.columns(3)

for i, (itype, info) in enumerate(INVOICE_TYPES.items()):
    col = cols[i % 3]
    s = summary.get(itype, {})
    uploaded = s.get("uploaded", False)
    rows = s.get("rows", 0)
    with col:
        status_icon = "✅" if uploaded else "⬜"
        color = info["color"] if uploaded else "#333"
        st.markdown(f"""
<div style='background:#0F1520;border:1px solid {color};border-radius:12px;
            padding:16px;margin-bottom:12px;'>
  <div style='font-size:1.4rem;'>{info["icon"]} {info["label"]}</div>
  <div style='color:{color};font-weight:700;margin-top:6px;'>
    {status_icon} {"Uploaded" if uploaded else "Not uploaded"}
  </div>
  <div style='color:#888;font-size:0.8rem;margin-top:4px;'>
    {rows} rows · {s.get("min_date","—")} → {s.get("max_date","—")}
  </div>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── Totals ────────────────────────────────────────────────────────────────────
totals = get_totals()
st.markdown("### 💰 Overall P&L")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue",    f"₹{totals['revenue']:,.0f}")
c2.metric("Total Costs",f"₹{totals['total_cost']:,.0f}")
c3.metric("Net Profit", f"₹{totals['profit']:,.0f}",
          delta=f"{totals['margin_pct']}% margin")
c4.metric("Margin",     f"{totals['margin_pct']}%")

# ── Cost waterfall ────────────────────────────────────────────────────────────
if totals["revenue"] > 0:
    st.markdown("### 🧱 Cost Waterfall")

    labels = ["Revenue", "FBA Fees", "Shipping", "Storage", "Advertising", "Returns", "Net Profit"]
    values = [
        totals["revenue"],
        -totals["fba_fees"],
        -totals["shipping"],
        -totals["storage"],
        -totals["advertising"],
        -totals["returns"],
        totals["profit"],
    ]

    fig = go.Figure(go.Waterfall(
        name="P&L",
        orientation="v",
        measure=["absolute", "relative", "relative", "relative", "relative", "relative", "total"],
        x=labels,
        y=values,
        decreasing={"marker": {"color": "#E8452C"}},
        increasing={"marker": {"color": "#2ECC71"}},
        totals={"marker": {"color": "#F5A623"}},
        connector={"line": {"color": "#1C2333"}},
    ))
    fig.update_layout(
        template="plotly_dark",
        plot_bgcolor="#0F1520",
        paper_bgcolor="#0F1520",
        font={"family": "Syne", "color": "#E8EAF0"},
        margin={"t": 30, "b": 30},
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Upload invoices to see the P&L waterfall chart.")
