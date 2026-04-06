import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from profit_calc import build_pnl, build_daily_trend, get_totals
from store import load_invoice, INVOICE_TYPES

st.markdown("# 📊 Dashboard")

trend_all = build_daily_trend()

if trend_all.empty:
    st.info("📤 No data yet — upload at least one invoice on the Upload page.")
    st.stop()

trend_all["date"] = pd.to_datetime(trend_all["date"])
min_date = trend_all["date"].min().date()
max_date = trend_all["date"].max().date()

fc1, fc2 = st.columns(2)
start = fc1.date_input("From", min_date)
end   = fc2.date_input("To",   max_date)

totals = get_totals(start, end)
trend  = build_daily_trend(start, end)
pnl    = build_pnl(start, end)

st.divider()
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("💰 Revenue",     f"₹{totals['revenue']:,.0f}")
k2.metric("📦 FBA Fees",    f"₹{totals['fba_fees']:,.0f}")
k3.metric("🚚 Shipping",    f"₹{totals['shipping']:,.0f}")
k4.metric("📣 Advertising", f"₹{totals['advertising']:,.0f}")
k5.metric("↩️ Returns",     f"₹{totals['returns']:,.0f}")

k6, k7, k8 = st.columns(3)
k6.metric("🏭 Storage",    f"₹{totals['storage']:,.0f}")
k7.metric("💸 Total Cost", f"₹{totals['total_cost']:,.0f}")
k8.metric("📈 Net Profit", f"₹{totals['profit']:,.0f}",
          delta=f"{totals['margin_pct']}% margin",
          delta_color="normal" if totals["profit"] >= 0 else "inverse")

rev    = totals["revenue"]
prof   = totals["profit"]
margin = totals["margin_pct"]

if prof < 0:
    st.error("⚠️ **You are operating at a LOSS.** Total costs exceed revenue.")
elif margin < 10:
    st.warning(f"⚠️ **Very thin margin ({margin}%).** Review your cost structure.")
elif margin < 20:
    st.warning(f"⚠️ Low margin ({margin}%). Consider reducing fees or increasing price.")
else:
    st.success(f"✅ Healthy margin of {margin}%. Keep it up!")

if totals["advertising"] > rev * 0.3:
    st.warning("📣 Advertising consuming >30% of revenue (ACoS too high).")
if totals["returns"] > rev * 0.15:
    st.warning("↩️ Returns above 15% of revenue. Check product quality / listings.")
if totals["fba_fees"] > rev * 0.4:
    st.warning("📦 FBA fees above 40% of revenue. Consider optimising packaging.")

st.divider()

col_pie, col_bar = st.columns(2)

with col_pie:
    st.markdown("#### 🥧 Cost Breakdown")
    cost_labels = ["FBA Fees", "Shipping", "Storage", "Advertising", "Returns"]
    cost_vals   = [totals["fba_fees"], totals["shipping"], totals["storage"],
                   totals["advertising"], totals["returns"]]
    colors      = ["#E8452C", "#F5A623", "#7B61FF", "#00C6FF", "#FF6B6B"]
    fig_pie = go.Figure(go.Pie(
        labels=cost_labels, values=cost_vals, hole=0.45,
        marker_colors=colors, textfont_size=12,
    ))
    fig_pie.update_layout(
        template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
        margin={"t":20,"b":20,"l":0,"r":0}, showlegend=True,
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    st.markdown("#### 📊 Revenue vs Profit vs Cost")
    summary_bar = pd.DataFrame({
        "Category": ["Revenue", "Total Cost", "Net Profit"],
        "Amount":   [totals["revenue"], totals["total_cost"], max(totals["profit"], 0)],
    })
    fig_bar = px.bar(summary_bar, x="Category", y="Amount", color="Category",
                     color_discrete_map={"Revenue":"#2ECC71","Total Cost":"#E8452C","Net Profit":"#F5A623"})
    fig_bar.update_layout(
        template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
        showlegend=False, margin={"t":20,"b":20},
    )
    st.plotly_chart(fig_bar, use_container_width=True)

if not trend.empty:
    st.markdown("#### 📈 Daily Revenue & Profit Trend")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(
        x=trend["date"], y=trend["revenue"], name="Revenue",
        line={"color":"#2ECC71","width":2}, fill="tozeroy", fillcolor="rgba(46,204,113,0.1)",
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend["date"], y=trend["profit"], name="Profit",
        line={"color":"#F5A623","width":2},
    ))
    fig_trend.add_trace(go.Scatter(
        x=trend["date"], y=trend["total_cost"], name="Total Cost",
        line={"color":"#E8452C","width":1.5,"dash":"dot"},
    ))
    fig_trend.update_layout(
        template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
        margin={"t":10,"b":30}, legend={"orientation":"h","yanchor":"bottom","y":1.02},
        xaxis_title="Date", yaxis_title="₹",
    )
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()
st.markdown("### 📦 Per-SKU Profit Breakdown")

if not pnl.empty:
    def highlight_profit(row):
        if row.get("profit", 0) < 0:
            return ["background-color: #2A0F0F"] * len(row)
        elif row.get("margin_pct", 0) < 10:
            return ["background-color: #2A1F0F"] * len(row)
        return [""] * len(row)

    display_cols = ["sku", "revenue", "fba_fees", "shipping", "storage",
                    "advertising", "returns", "total_cost", "profit", "margin_pct"]
    show_cols = [c for c in display_cols if c in pnl.columns]
    styled = pnl[show_cols].style.apply(highlight_profit, axis=1).format(
        {c: "₹{:,.0f}" for c in show_cols if c not in ("sku", "margin_pct")}
    ).format({"margin_pct": "{:.1f}%"})
    st.dataframe(styled, use_container_width=True)

    st.markdown("#### 🏆 Profit by SKU")
    fig_sku = px.bar(
        pnl.head(20), x="sku", y="profit", color="profit",
        color_continuous_scale=["#E8452C", "#F5A623", "#2ECC71"],
        labels={"profit": "Net Profit (₹)", "sku": "SKU"},
    )
    fig_sku.update_layout(
        template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
        margin={"t":10,"b":30}, coloraxis_showscale=False,
    )
    st.plotly_chart(fig_sku, use_container_width=True)

    loss = pnl[pnl["profit"] < 0]
    if not loss.empty:
        st.error(f"⚠️ **{len(loss)} loss-making SKU(s) detected:**")
        st.dataframe(loss[show_cols], use_container_width=True)
else:
    st.info("Upload invoices with SKU/ASIN data to see per-SKU breakdown.")
