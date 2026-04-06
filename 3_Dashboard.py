import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# ── Inline store ──────────────────────────────────────────────────────────────
INVOICE_TYPES = {
    "fba_fees":    {"label": "FBA Fees",          "icon": "📦", "color": "#E8452C"},
    "shipping":    {"label": "Shipping / Courier", "icon": "🚚", "color": "#F5A623"},
    "storage":     {"label": "Storage Fees",       "icon": "🏭", "color": "#7B61FF"},
    "advertising": {"label": "Advertising (PPC)",  "icon": "📣", "color": "#00C6FF"},
    "returns":     {"label": "Returns / Refunds",  "icon": "↩️",  "color": "#FF6B6B"},
    "sales":       {"label": "Sales Revenue",      "icon": "💰", "color": "#2ECC71"},
}
STORE_KEY = "forecastly_invoices"
COST_TYPES    = ["fba_fees","shipping","storage","advertising","returns"]
REVENUE_TYPES = ["sales"]

def _get_store():
    if STORE_KEY not in st.session_state:
        st.session_state[STORE_KEY] = {}
    return st.session_state[STORE_KEY]

def load_all():
    store = _get_store()
    return {k: v for k, v in store.items() if v is not None and not v.empty}

# ── Inline amount/sku detection ───────────────────────────────────────────────
def detect_amount_column(df):
    priority = ["amount","total","value","price","revenue","sales",
                "fee","cost","spend","charge","net","gross","settlement","payment","refund"]
    cols_lower = {c.lower(): c for c in df.columns}
    for kw in priority:
        for cl, co in cols_lower.items():
            if kw in cl:
                try:
                    s = df[co].astype(str).str.replace(",","").str.replace("₹","").str.strip()
                    if pd.to_numeric(s, errors="coerce").notna().sum() > 0:
                        return co
                except: continue
    return None

def detect_sku_column(df):
    keywords = ["sku","asin","product","item","listing","fnsku","msku"]
    cols_lower = {c.lower(): c for c in df.columns}
    for kw in keywords:
        for cl, co in cols_lower.items():
            if kw in cl:
                return co
    return None

# ── Inline profit calc ────────────────────────────────────────────────────────
def build_daily_trend(date_start=None, date_end=None):
    data = load_all()
    if not data: return pd.DataFrame()
    records = []
    for itype, df in data.items():
        if df is None or df.empty or "date" not in df.columns: continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if date_start: df = df[df["date"] >= pd.to_datetime(date_start)]
        if date_end:   df = df[df["date"] <= pd.to_datetime(date_end)]
        col = detect_amount_column(df)
        if col:
            s = df[col].astype(str).str.replace(",","").str.replace("₹","")
            df["amount"] = pd.to_numeric(s, errors="coerce").fillna(0)
            df["invoice_type"] = itype
            records.append(df[["date","invoice_type","amount"]])
    if not records: return pd.DataFrame()
    long = pd.concat(records, ignore_index=True)
    long["date"] = long["date"].dt.date
    pivot = long.groupby(["date","invoice_type"])["amount"].sum().unstack(fill_value=0)
    for col in COST_TYPES + REVENUE_TYPES:
        if col not in pivot.columns: pivot[col] = 0.0
    pivot = pivot.reset_index()
    pivot["revenue"]    = pivot.get("sales", 0)
    pivot["total_cost"] = sum(pivot.get(c, 0) for c in COST_TYPES)
    pivot["profit"]     = pivot["revenue"] - pivot["total_cost"]
    return pivot.sort_values("date")

def build_pnl(date_start=None, date_end=None):
    data = load_all()
    if not data: return pd.DataFrame()
    records = []
    for itype, df in data.items():
        if df is None or df.empty: continue
        if "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            if date_start: df = df[df["date"] >= pd.to_datetime(date_start)]
            if date_end:   df = df[df["date"] <= pd.to_datetime(date_end)]
        amounts = []
        col = detect_amount_column(df)
        if col:
            s = df[col].astype(str).str.replace(",","").str.replace("₹","").str.strip()
            amounts = pd.to_numeric(s, errors="coerce").fillna(0).tolist()
        sku_col = detect_sku_column(df)
        skus = df[sku_col].astype(str).str.strip().tolist() if sku_col else ["UNKNOWN"] * len(df)
        for amt, sku in zip(amounts, skus):
            records.append({"sku": sku, "invoice_type": itype, "amount": amt})
    if not records: return pd.DataFrame()
    long = pd.DataFrame(records)
    pnl  = long.groupby(["sku","invoice_type"])["amount"].sum().unstack(fill_value=0)
    for col in COST_TYPES + REVENUE_TYPES:
        if col not in pnl.columns: pnl[col] = 0.0
    pnl = pnl.reset_index()
    pnl["revenue"]    = pnl.get("sales", 0)
    pnl["total_cost"] = sum(pnl.get(c, 0) for c in COST_TYPES)
    pnl["profit"]     = pnl["revenue"] - pnl["total_cost"]
    pnl["margin_pct"] = np.where(pnl["revenue"] != 0, (pnl["profit"]/pnl["revenue"]*100).round(1), 0)
    return pnl.sort_values("profit", ascending=False)

def get_totals(date_start=None, date_end=None):
    trend = build_daily_trend(date_start, date_end)
    if trend.empty:
        return {k: 0 for k in ["revenue","fba_fees","shipping","storage","advertising","returns","total_cost","profit","margin_pct"]}
    rev  = trend["revenue"].sum()
    cost = trend["total_cost"].sum()
    prof = trend["profit"].sum()
    return {
        "revenue": rev, "total_cost": cost, "profit": prof,
        "margin_pct": round(prof/rev*100, 1) if rev else 0,
        **{c: trend[c].sum() if c in trend.columns else 0 for c in COST_TYPES}
    }

# ── Page UI ───────────────────────────────────────────────────────────────────
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
k8.metric("📈 Net Profit", f"₹{totals['profit']:,.0f}", delta=f"{totals['margin_pct']}% margin",
          delta_color="normal" if totals["profit"] >= 0 else "inverse")

rev, prof, margin = totals["revenue"], totals["profit"], totals["margin_pct"]
if prof < 0:         st.error("⚠️ **Operating at a LOSS.** Total costs exceed revenue.")
elif margin < 10:    st.warning(f"⚠️ Very thin margin ({margin}%). Review cost structure.")
elif margin < 20:    st.warning(f"⚠️ Low margin ({margin}%). Consider reducing fees.")
else:                st.success(f"✅ Healthy margin of {margin}%!")
if totals["advertising"] > rev * 0.3: st.warning("📣 Ad spend >30% of revenue (ACoS too high).")
if totals["returns"]     > rev * 0.15: st.warning("↩️ Returns above 15% of revenue.")
if totals["fba_fees"]    > rev * 0.4:  st.warning("📦 FBA fees above 40% of revenue.")

st.divider()
col_pie, col_bar = st.columns(2)
with col_pie:
    st.markdown("#### 🥧 Cost Breakdown")
    fig_pie = go.Figure(go.Pie(
        labels=["FBA Fees","Shipping","Storage","Advertising","Returns"],
        values=[totals["fba_fees"],totals["shipping"],totals["storage"],totals["advertising"],totals["returns"]],
        hole=0.45, marker_colors=["#E8452C","#F5A623","#7B61FF","#00C6FF","#FF6B6B"], textfont_size=12,
    ))
    fig_pie.update_layout(template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
                          margin={"t":20,"b":20,"l":0,"r":0})
    st.plotly_chart(fig_pie, use_container_width=True)

with col_bar:
    st.markdown("#### 📊 Revenue vs Profit vs Cost")
    fig_bar = px.bar(
        pd.DataFrame({"Category":["Revenue","Total Cost","Net Profit"],
                      "Amount":[totals["revenue"],totals["total_cost"],max(totals["profit"],0)]}),
        x="Category", y="Amount", color="Category",
        color_discrete_map={"Revenue":"#2ECC71","Total Cost":"#E8452C","Net Profit":"#F5A623"},
    )
    fig_bar.update_layout(template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
                          showlegend=False, margin={"t":20,"b":20})
    st.plotly_chart(fig_bar, use_container_width=True)

if not trend.empty:
    st.markdown("#### 📈 Daily Revenue & Profit Trend")
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=trend["date"], y=trend["revenue"], name="Revenue",
        line={"color":"#2ECC71","width":2}, fill="tozeroy", fillcolor="rgba(46,204,113,0.1)"))
    fig_trend.add_trace(go.Scatter(x=trend["date"], y=trend["profit"], name="Profit",
        line={"color":"#F5A623","width":2}))
    fig_trend.add_trace(go.Scatter(x=trend["date"], y=trend["total_cost"], name="Total Cost",
        line={"color":"#E8452C","width":1.5,"dash":"dot"}))
    fig_trend.update_layout(template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
        margin={"t":10,"b":30}, legend={"orientation":"h","yanchor":"bottom","y":1.02},
        xaxis_title="Date", yaxis_title="₹")
    st.plotly_chart(fig_trend, use_container_width=True)

st.divider()
st.markdown("### 📦 Per-SKU Profit Breakdown")
if not pnl.empty:
    def highlight_profit(row):
        if row.get("profit", 0) < 0:     return ["background-color:#2A0F0F"] * len(row)
        if row.get("margin_pct", 0) < 10: return ["background-color:#2A1F0F"] * len(row)
        return [""] * len(row)
    display_cols = ["sku","revenue","fba_fees","shipping","storage","advertising","returns","total_cost","profit","margin_pct"]
    show_cols = [c for c in display_cols if c in pnl.columns]
    styled = pnl[show_cols].style.apply(highlight_profit, axis=1)\
        .format({c: "₹{:,.0f}" for c in show_cols if c not in ("sku","margin_pct")})\
        .format({"margin_pct": "{:.1f}%"})
    st.dataframe(styled, use_container_width=True)

    fig_sku = px.bar(pnl.head(20), x="sku", y="profit", color="profit",
        color_continuous_scale=["#E8452C","#F5A623","#2ECC71"],
        labels={"profit":"Net Profit (₹)","sku":"SKU"})
    fig_sku.update_layout(template="plotly_dark", paper_bgcolor="#0F1520", plot_bgcolor="#0F1520",
        margin={"t":10,"b":30}, coloraxis_showscale=False)
    st.plotly_chart(fig_sku, use_container_width=True)

    loss = pnl[pnl["profit"] < 0]
    if not loss.empty:
        st.error(f"⚠️ **{len(loss)} loss-making SKU(s):**")
        st.dataframe(loss[show_cols], use_container_width=True)
else:
    st.info("Upload invoices with SKU/ASIN data to see per-SKU breakdown.")
