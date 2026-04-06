import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import tempfile
import os
from datetime import datetime
 
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Image,
    Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame
from utils.forecast import run_neuralprophet_forecast
from utils.forecast import detect_anomalies, run_pycaret_forecast
from utils.profit_calc import build_daily_trend
from utils.forecast import (
    run_forecast,
    run_prophet_forecast,
    run_xgb_forecast,
    run_arima_forecast,
    calculate_mape
)
 
# ─── BRAND COLORS (Light/White Theme) ────────────────────────────────────────
BRAND_DARK    = colors.HexColor("#1E293B")       # dark text / header bg
BRAND_CARD    = colors.HexColor("#F1F5F9")       # card background
BRAND_ACCENT  = colors.HexColor("#0284C7")       # primary accent (blue)
BRAND_GREEN   = colors.HexColor("#16A34A")
BRAND_RED     = colors.HexColor("#DC2626")
BRAND_YELLOW  = colors.HexColor("#D97706")
BRAND_TEXT    = colors.HexColor("#1E293B")       # main body text
BRAND_MUTED   = colors.HexColor("#64748B")       # muted/secondary text
BRAND_WHITE   = colors.white                     # page background
 
# 🎨 GLOBAL STYLE
st.markdown("""
<style>
.block-container { padding: 1rem; max-width: 100%; }
.main { background-color:#0F172A; }
h1,h2,h3 { color:#E2E8F0; }
[data-testid="stMetric"] {
    background:#111827;
    padding:10px;
    border-radius:10px;
    border:1px solid #1F2937;
}
@media (max-width: 768px) {
    h1 { font-size: 22px !important; }
    h2 { font-size: 18px !important; }
    [data-testid="stMetric"] { font-size: 14px !important; padding:8px; }
    div[data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
    .stButton>button { width: 100%; }
    .element-container { margin-bottom: 10px; }
}
</style>
""", unsafe_allow_html=True)
 
# 🚀 HERO HEADER
st.markdown("""
<div style="padding:25px;border-radius:16px;
background:linear-gradient(90deg,#1E293B,#0F172A);
box-shadow:0 0 20px rgba(0,198,255,0.15);">
<h1>📈 Forecastly</h1>
<p style="color:#94A3B8;">AI-Powered Sales Forecasting & Profit Intelligence</p>
</div>
""", unsafe_allow_html=True)
 
trend = build_daily_trend()
trend = detect_anomalies(trend)
 
if trend.empty or "revenue" not in trend.columns or trend["revenue"].sum() == 0:
    st.info("📤 Upload your Sales Revenue invoice first.")
    st.stop()
 
trend["date"] = pd.to_datetime(trend["date"], errors="coerce")
trend = trend.sort_values("date")
 
col1, col2 = st.columns([1, 1], gap="small")
with col1:
    days = st.slider("Forecast horizon (days)", 7, 30, 14)
with col2:
    model_type = st.selectbox("Model", [
        "Auto (Best Model) 🤖",
        "Scikit-Learn (Fast)",
        "Prophet (Advanced)",
        "XGBoost (High Accuracy)",
        "ARIMA (Baseline)",
        "AutoML (PyCaret) 🧠",
        "NeuralProphet (Meta AI) 🧠🔥"
    ])
 
st.markdown("### 💰 Cost & Profit Settings")
c1, c2 = st.columns(2)
with c1:
    cost_pct = st.slider("Cost (% of Revenue)", 0, 100, 40)
with c2:
    fixed_cost = st.number_input("Fixed Daily Cost (₹)", value=500)
 
models = {
    "Scikit": run_forecast,
    "Prophet": run_prophet_forecast,
    "XGBoost": run_xgb_forecast,
    "ARIMA": run_arima_forecast,
    "NeuralProphet": run_neuralprophet_forecast
}
 
if model_type == "Auto (Best Model) 🤖":
    results, scores = {}, []
    for name, func in models.items():
        try:
            df_pred = func(trend, days=days)
            df_pred["date"] = pd.to_datetime(df_pred["date"])
            hist_tmp = df_pred[~df_pred["is_future"]]
            score = calculate_mape(hist_tmp["actual"], hist_tmp["predicted"]) if "actual" in hist_tmp and "predicted" in hist_tmp else 999
            results[name] = df_pred
            scores.append((name, score))
        except:
            pass
    score_df = pd.DataFrame(scores, columns=["Model", "MAPE"]).sort_values("MAPE")
    best_model = score_df.iloc[0]["Model"]
    forecast_df = results[best_model]
    st.markdown("### 🤖 Model Comparison")
    st.dataframe(score_df, use_container_width=True)
    st.success(f"🏆 Forecastly selected best model: {best_model}")
elif model_type == "Prophet (Advanced)":
    forecast_df = run_prophet_forecast(trend, days=days)
elif model_type == "XGBoost (High Accuracy)":
    forecast_df = run_xgb_forecast(trend, days=days)
elif model_type == "ARIMA (Baseline)":
    forecast_df = run_arima_forecast(trend, days=days)
elif model_type == "AutoML (PyCaret) 🧠":
    forecast_df = run_pycaret_forecast(trend, days=days)
elif model_type == "NeuralProphet (Meta AI) 🧠🔥":
    forecast_df = run_neuralprophet_forecast(trend, days=days)
else:
    forecast_df = run_forecast(trend, days=days)
 
if forecast_df.empty:
    st.warning("Not enough data.")
    st.stop()
 
forecast_df["date"] = pd.to_datetime(forecast_df["date"])
hist = forecast_df[~forecast_df["is_future"]].copy()
future = forecast_df[forecast_df["is_future"]].copy()
 
future["cost"] = (future["predicted"] * cost_pct / 100) + fixed_cost
future["profit"] = future["predicted"] - future["cost"]
 
st.markdown("## 🎮 Scenario Simulator")
discount = st.slider("Discount %", 0, 50, 10)
future["simulated_revenue"] = future["predicted"] * (1 - discount / 100)
future["simulated_profit"] = future["simulated_revenue"] - future["cost"]
st.line_chart(future[["simulated_revenue", "simulated_profit"]])
 
st.markdown("""
<div style="background:#111827;padding:15px;border-radius:12px;">
<h3>📊 Forecast Overview</h3>
</div>
""", unsafe_allow_html=True)
 
fig = go.Figure()
if "upper" in future.columns:
    fig.add_trace(go.Scatter(
        x=pd.concat([future["date"], future["date"][::-1]]),
        y=pd.concat([future["upper"], future["lower"][::-1]]),
        fill="toself", fillcolor="rgba(0,198,255,0.1)",
        line=dict(color="rgba(0,0,0,0)")
    ))
fig.add_trace(go.Scatter(x=hist["date"], y=hist.get("actual", hist.get("predicted")), name="Actual", line=dict(color="#2ECC71")))
fig.add_trace(go.Scatter(x=future["date"], y=future["predicted"], name="Forecast", line=dict(color="#00C6FF")))
fig.update_layout(template="plotly_dark", paper_bgcolor="#0F172A", plot_bgcolor="#0F172A",
                  font={"color": "#E2E8F0"}, legend={"orientation": "h"}, margin=dict(t=30, b=30))
st.plotly_chart(fig, use_container_width=True)
 
st.markdown("## 💰 Profit vs Revenue")
fig2 = go.Figure()
fig2.add_trace(go.Scatter(x=future["date"], y=future["predicted"], name="Revenue"))
fig2.add_trace(go.Scatter(x=future["date"], y=future["profit"], name="Profit"))
fig2.update_layout(template="plotly_dark")
st.plotly_chart(fig2, use_container_width=True)
 
st.markdown("## 🚨 Anomaly Detection")
anomalies = trend[trend["anomaly"] == 1]
if not anomalies.empty:
    st.warning(f"{len(anomalies)} anomalies detected in your sales data")
    st.dataframe(anomalies[["date", "revenue"]])
else:
    st.success("No anomalies detected")
 
st.markdown("## 📅 Forecast Table")
future_display = future[["date", "predicted"]].copy()
future_display.columns = ["Date", "Revenue"]
future_display["Date"] = future_display["Date"].dt.strftime("%d %b %Y")
st.dataframe(future_display, use_container_width=True)
 
pred_total = future["predicted"].sum()
total_profit = future["profit"].sum()
profit_margin = (total_profit / (pred_total + 1e-5)) * 100
confidence = max(0, 100 - (profit_margin if profit_margin else 20))
 
c1, c2, c3, c4 = st.columns(4)
c1.metric("Revenue", f"₹{pred_total:,.0f}")
c2.metric("Profit", f"₹{total_profit:,.0f}")
c3.metric("Margin", f"{profit_margin:.1f}%")
c4.metric("Confidence", f"{confidence:.1f}%")
 
st.markdown("## 💡 Business Insights")
recent = hist.get("actual", hist.get("predicted")).dropna().tail(7)
future_vals = future["predicted"].head(7)
growth = None
if len(recent) > 0:
    growth = ((future_vals.mean() - recent.mean()) / (recent.mean() + 1e-5)) * 100
    st.metric("Growth", f"{growth:.1f}%")
 
st.markdown("## 🤖 Smart AI Suggestions")
_hist_vals = hist["actual"] if "actual" in hist.columns else hist["predicted"]
recent = _hist_vals.dropna().tail(7)
future_vals = future["predicted"].head(7)
growth = None
if len(recent) > 0:
    growth = ((future_vals.mean() - recent.mean()) / (recent.mean() + 1e-5)) * 100
 
profit_margin = (total_profit / (pred_total + 1e-5)) * 100
volatility = _hist_vals.std() / (_hist_vals.mean() + 1e-5)
trend["day"] = trend["date"].dt.day_name()
seasonality = trend.groupby("day")["revenue"].mean()
best_day = seasonality.idxmax() if not seasonality.empty else "N/A"
worst_day = seasonality.idxmin() if not seasonality.empty else "N/A"
ad_efficiency = profit_margin - abs(growth if growth else 0)
 
if profit_margin < 10:
    category_type = "Low-margin category"
elif growth and growth > 10:
    category_type = "Trending category"
else:
    category_type = "Stable category"
 
st.markdown("### 📊 Business Health Overview")
c1, c2, c3 = st.columns(3)
c1.metric("Growth", f"{growth:.1f}%" if growth else "N/A")
c2.metric("Profit Margin", f"{profit_margin:.1f}%")
c3.metric("Risk Level", "High" if volatility > 0.5 else "Low")
 
if total_profit < 0:
    st.error("🚨 Forecastly detected negative profitability")
    st.markdown(f"""
### 🔻 Critical Fix Required
- Operating in **{category_type}**
- Immediate cost reduction needed  
### 📢 Ads Strategy
- Pause low ROI campaigns  
- Focus on conversion-driven ads  
### ⚙️ Actions
- Cut 10–20% costs  
- Reprice products  
- Remove loss-making SKUs  
""")
elif growth is not None and growth < 0:
    st.warning("📉 Forecastly detected declining demand")
    st.markdown(f"""
### 📉 Recovery Strategy
- Category: **{category_type}**
### 📢 Ads Optimization
- Retarget customers  
- Improve creatives  
### 📅 Timing Insight
- Best day: **{best_day}**
### 🎯 Actions
- Discounts  
- SEO improvements  
""")
elif profit_margin < 10:
    st.warning("⚠️ Forecastly detected low margins")
    st.markdown(f"""
### 💰 Margin Optimization
- Category: **{category_type}**
### 🧠 Improvements
- Increase pricing slightly  
- Bundle products  
### 📢 Ads
- Focus high AOV users  
### 📊 Efficiency Score
- {ad_efficiency:.1f}
""")
elif growth is not None and growth > 10:
    st.success("🚀 Forecastly detected strong growth")
    st.markdown(f"""
### 🚀 Scale Strategy
- Category: **{category_type}**
### 📈 Actions
- Increase ad spend  
- Expand inventory  
### 📅 Peak Insight
- Best day: **{best_day}**
### 🏆 Pro Tip
- Secure supply chain early  
""")
else:
    st.info("📊 Forecastly detected stable performance")
    st.markdown(f"""
### ⚖️ Optimization Mode
- Category: **{category_type}**
### 📈 Strategy
- A/B testing  
- Conversion optimization  
### 📅 Insights
- Best day: **{best_day}**
- Weak day: **{worst_day}**
### 🧠 Focus
- Retention  
- Branding  
""")
 
def generate_response(user_input):
    text = user_input.lower()
    if "profit" in text:
        if total_profit < 0:
            return "📉 You are currently in loss. Forecastly recommends reducing costs and stopping low ROI ads."
        elif profit_margin < 10:
            return "⚠️ Your profit margin is low. Consider increasing pricing or reducing costs."
        else:
            return "✅ Your profit looks healthy. You can scale your business."
    elif "growth" in text:
        if growth and growth > 10:
            return "🚀 Strong growth detected. This is a good time to scale ads and inventory."
        elif growth and growth < 0:
            return "📉 Sales are declining. You should optimize ads and improve listings."
        else:
            return "📊 Your growth is stable. Focus on optimization."
    elif "model" in text:
        return "🤖 You can use Auto mode for best accuracy or Ensemble for balanced results."
    elif "ads" in text:
        return "📢 Focus on high ROI campaigns and retargeting customers."
    elif "forecast" in text:
        return f"📊 Forecasted revenue for next {days} days is ₹{pred_total:,.0f}"
    else:
        return "🤖 Ask me about profit, growth, ads, forecast, or strategy!"
 
with st.expander("💬 Forecastly AI Assistant — click to open", expanded=False):
 
    # Quick suggestion buttons
    st.markdown("**Quick questions:**")
    qcols = st.columns(4)
    quick_questions = ["💰 How's my profit?", "📈 Show my growth", "📢 Ads advice", "📊 Forecast summary"]
    quick_clicked = None
    for i, q in enumerate(quick_questions):
        if qcols[i].button(q, key=f"quick_{i}", use_container_width=True):
            quick_clicked = q
 
    st.divider()
 
    if "messages" not in st.session_state:
        st.session_state.messages = []
 
    # Render chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
 
    # Handle quick button click
    if quick_clicked:
        st.session_state.messages.append({"role": "user", "content": quick_clicked})
        with st.chat_message("user"):
            st.markdown(quick_clicked)
        response = generate_response(quick_clicked)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
 
    # Handle typed input
    user_input = st.chat_input("Ask Forecastly anything about your business...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        response = generate_response(user_input)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response)
 
    # Clear chat button
    if st.session_state.get("messages"):
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# 📄 PROFESSIONAL PDF EXPORT
# ─────────────────────────────────────────────────────────────────────────────
 
st.markdown("## 📄 Export Report")
 
def generate_pdf():
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    tmp.close()
 
    PAGE_W, PAGE_H = A4
 
    # ── Custom styles ──────────────────────────────────────────────────────
    styles = getSampleStyleSheet()
 
    style_cover_title = ParagraphStyle(
        "CoverTitle",
        fontSize=28,
        textColor=BRAND_WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    style_cover_sub = ParagraphStyle(
        "CoverSub",
        fontSize=11,
        textColor=colors.HexColor("#94A3B8"),
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    style_section = ParagraphStyle(
        "Section",
        fontSize=13,
        textColor=BRAND_ACCENT,
        fontName="Helvetica-Bold",
        spaceBefore=18,
        spaceAfter=6,
    )
    style_body = ParagraphStyle(
        "Body",
        fontSize=9,
        textColor=colors.HexColor("#334155"),
        fontName="Helvetica",
        leading=14,
        spaceAfter=4,
    )
    style_footer = ParagraphStyle(
        "Footer",
        fontSize=8,
        textColor=BRAND_MUTED,
        fontName="Helvetica-Oblique",
        alignment=TA_CENTER,
    )
    style_insight = ParagraphStyle(
        "Insight",
        fontSize=10,
        textColor=colors.HexColor("#1E293B"),
        fontName="Helvetica",
        leading=16,
        spaceAfter=4,
        leftIndent=10,
    )
    style_cover_brand = ParagraphStyle(
        "CoverBrand",
        fontSize=36,
        textColor=BRAND_WHITE,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=2,
        leading=40,
    )
    style_cover_tagline = ParagraphStyle(
        "CoverTagline",
        fontSize=13,
        textColor=colors.HexColor("#7DD3FC"),
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=4,
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        fontSize=9,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    style_subheading = ParagraphStyle(
        "SubHeading",
        fontSize=10,
        textColor=BRAND_DARK,
        fontName="Helvetica-Bold",
        spaceAfter=4,
        spaceBefore=8,
    )
 
    # ── Page background + header/footer callbacks ──────────────────────────
    def draw_page(canvas, doc):
        canvas.saveState()
 
        # Full-page white background
        canvas.setFillColor(BRAND_WHITE)
        canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
 
        # Top accent bar (dark navy)
        canvas.setFillColor(BRAND_DARK)
        canvas.rect(0, PAGE_H - 40, PAGE_W, 40, fill=1, stroke=0)
 
        # Top bar: logo text
        canvas.setFont("Helvetica-Bold", 13)
        canvas.setFillColor(colors.white)
        canvas.drawString(40, PAGE_H - 27, "Forecastly")
 
        # Top bar: right-side date
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.HexColor("#94A3B8"))
        canvas.drawRightString(PAGE_W - 40, PAGE_H - 27, datetime.now().strftime("%d %b %Y"))
 
        # Thin accent line below header
        canvas.setFillColor(BRAND_ACCENT)
        canvas.rect(0, PAGE_H - 43, PAGE_W, 3, fill=1, stroke=0)
 
        # Bottom footer bar (light grey)
        canvas.setFillColor(colors.HexColor("#F1F5F9"))
        canvas.rect(0, 0, PAGE_W, 32, fill=1, stroke=0)
 
        # Footer top border
        canvas.setFillColor(colors.HexColor("#CBD5E1"))
        canvas.rect(0, 32, PAGE_W, 1, fill=1, stroke=0)
 
        # Footer text
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(BRAND_MUTED)
        canvas.drawString(40, 11, f"Generated by Forecastly  •  AI Business Intelligence")
        canvas.drawRightString(PAGE_W - 40, 11, f"Page {doc.page}")
 
        # Left accent stripe
        canvas.setFillColor(BRAND_ACCENT)
        canvas.rect(0, 33, 3, PAGE_H - 76, fill=1, stroke=0)
 
        canvas.restoreState()
 
    # ── Build document ─────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        tmp.name,
        pagesize=A4,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.65 * inch,
    )
 
    elements = []
 
    # ── COVER PAGE (branded hero block) ───────────────────────────────────
    model_clean = model_type.encode("ascii", "ignore").decode()  # strip emojis for PDF
 
    # Dedicated styles so ReportLab measures row heights correctly
    style_hero_title = ParagraphStyle(
        "HeroTitle",
        fontSize=32,
        leading=40,
        textColor=colors.white,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    )
    style_hero_sub = ParagraphStyle(
        "HeroSub",
        fontSize=13,
        leading=18,
        textColor=colors.HexColor("#7DD3FC"),
        fontName="Helvetica",
        alignment=TA_LEFT,
    )
    style_hero_meta = ParagraphStyle(
        "HeroMeta",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#94A3B8"),
        fontName="Helvetica",
        alignment=TA_LEFT,
    )
 
    hero_data = [
        [Paragraph("Forecastly", style_hero_title)],
        [Paragraph("AI-Powered Business Intelligence Report", style_hero_sub)],
        [Paragraph(
            f'<font color="#94A3B8">Generated: </font>'
            f'<font color="#E2E8F0"><b>{datetime.now().strftime("%d %b %Y, %H:%M")}</b></font>'
            f'&nbsp;&nbsp;|&nbsp;&nbsp;'
            f'<font color="#94A3B8">Model: </font>'
            f'<font color="#00C6FF"><b>{model_clean}</b></font>'
            f'&nbsp;&nbsp;|&nbsp;&nbsp;'
            f'<font color="#94A3B8">Horizon: </font>'
            f'<font color="#E2E8F0"><b>{days} days</b></font>',
            style_hero_meta
        )],
    ]
    hero_table = Table(
        hero_data,
        colWidths=[PAGE_W - 1.2 * inch],
        rowHeights=[48, 26, 20],   # explicit heights prevent overlap
    )
    hero_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_DARK),
        ("TOPPADDING",    (0, 0), (-1, 0), 20),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
        ("TOPPADDING",    (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("TOPPADDING",    (0, 2), (-1, 2), 6),
        ("BOTTOMPADDING", (0, 2), (-1, 2), 18),
        ("LEFTPADDING",   (0, 0), (-1, -1), 28),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 28),
        ("LINEABOVE",     (0, 2), (-1, 2), 1, colors.HexColor("#334155")),
        ("LINEBELOW",     (0, -1), (-1, -1), 4, BRAND_ACCENT),
    ]))
    elements.append(hero_table)
    elements.append(Spacer(1, 12))
 
    # Quick-stat strip
    margin_color_hex_qs = "#16A34A" if profit_margin >= 20 else ("#D97706" if profit_margin >= 10 else "#DC2626")
    profit_color_hex_qs = "#16A34A" if total_profit >= 0 else "#DC2626"
    growth_color_hex_qs = "#16A34A" if (growth or 0) >= 0 else "#DC2626"
 
    qs_inner = [
        [Paragraph('<font color="#64748B" size="8">FORECAST REVENUE</font>', style_body),
         Paragraph('<font color="#64748B" size="8">NET PROFIT</font>', style_body),
         Paragraph('<font color="#64748B" size="8">PROFIT MARGIN</font>', style_body),
         Paragraph('<font color="#64748B" size="8">GROWTH RATE</font>', style_body),
         Paragraph('<font color="#64748B" size="8">CONFIDENCE</font>', style_body)],
        [Paragraph(f'<font color="#0284C7" size="15"><b>Rs.{pred_total:,.0f}</b></font>', style_body),
         Paragraph(f'<font color="{profit_color_hex_qs}" size="15"><b>Rs.{total_profit:,.0f}</b></font>', style_body),
         Paragraph(f'<font color="{margin_color_hex_qs}" size="15"><b>{profit_margin:.1f}%</b></font>', style_body),
         Paragraph(f'<font color="{growth_color_hex_qs}" size="15"><b>{f"{growth:.1f}%" if growth else "N/A"}</b></font>', style_body),
         Paragraph(f'<font color="#0284C7" size="15"><b>{confidence:.1f}%</b></font>', style_body)],
    ]
    qs_col = (PAGE_W - 1.2 * inch) / 5
    qs_table = Table(qs_inner, colWidths=[qs_col] * 5, rowHeights=[20, 38])
    qs_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_CARD),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("LINEAFTER",     (0, 0), (3, -1), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, -1), (-1, -1), 3, BRAND_ACCENT),
    ]))
    elements.append(qs_table)
    elements.append(Spacer(1, 20))
 
    # ── KPI CARDS ──────────────────────────────────────────────────────────
    elements.append(Paragraph("KEY PERFORMANCE INDICATORS", style_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
    def kpi_cell(label, value, color=BRAND_ACCENT):
        return [
            Paragraph(f'<font color="#94A3B8" size="8">{label}</font>', style_body),
            Paragraph(f'<font color="{color.hexval()}" size="16"><b>{value}</b></font>', style_body),
        ]
 
    margin_color = BRAND_GREEN if profit_margin >= 20 else (BRAND_YELLOW if profit_margin >= 10 else BRAND_RED)
    profit_color = BRAND_GREEN if total_profit >= 0 else BRAND_RED
    growth_color = BRAND_GREEN if (growth or 0) >= 0 else BRAND_RED
 
    kpi_inner = [
        [Paragraph('<font color="#64748B" size="8">TOTAL REVENUE</font>', style_body),
         Paragraph('<font color="#64748B" size="8">NET PROFIT</font>', style_body),
         Paragraph('<font color="#64748B" size="8">PROFIT MARGIN</font>', style_body),
         Paragraph('<font color="#64748B" size="8">GROWTH</font>', style_body)],
        [Paragraph(f'<font color="#0284C7" size="15"><b>Rs.{pred_total:,.0f}</b></font>', style_body),
         Paragraph(f'<font color="{profit_color.hexval()}" size="15"><b>Rs.{total_profit:,.0f}</b></font>', style_body),
         Paragraph(f'<font color="{margin_color.hexval()}" size="15"><b>{profit_margin:.1f}%</b></font>', style_body),
         Paragraph(f'<font color="{growth_color.hexval()}" size="15"><b>{f"{growth:.1f}%" if growth else "N/A"}</b></font>', style_body)],
    ]
 
    col_w = (PAGE_W - 1.2 * inch) / 4
    kpi_table = Table(kpi_inner, colWidths=[col_w] * 4, rowHeights=[22, 36])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_CARD),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEAFTER",     (0, 0), (2, -1), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, -1), (-1, -1), 2, BRAND_ACCENT),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 6))
 
    # Extra KPIs row
    extra_data = [
        [Paragraph('<font color="#64748B" size="8">FORECAST DAYS</font>', style_body),
         Paragraph('<font color="#64748B" size="8">COST %</font>', style_body),
         Paragraph('<font color="#64748B" size="8">FIXED DAILY COST</font>', style_body),
         Paragraph('<font color="#64748B" size="8">CONFIDENCE</font>', style_body)],
        [Paragraph(f'<font color="#1E293B" size="13"><b>{days} days</b></font>', style_body),
         Paragraph(f'<font color="#1E293B" size="13"><b>{cost_pct}%</b></font>', style_body),
         Paragraph(f'<font color="#1E293B" size="13"><b>Rs.{fixed_cost:,.0f}</b></font>', style_body),
         Paragraph(f'<font color="#1E293B" size="13"><b>{confidence:.1f}%</b></font>', style_body)],
    ]
    extra_table = Table(extra_data, colWidths=[col_w] * 4, rowHeights=[22, 30])
    extra_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEAFTER",     (0, 0), (2, -1), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1, colors.HexColor("#CBD5E1")),
    ]))
    elements.append(extra_table)
    elements.append(Spacer(1, 16))
 
    # ── CHARTS ─────────────────────────────────────────────────────────────
    chart_path = tmp.name + "_forecast.png"
    profit_chart_path = tmp.name + "_profit.png"
    charts_ok = False
 
    try:
        fig.write_image(chart_path, width=900, height=380, scale=2)
        fig2.write_image(profit_chart_path, width=900, height=340, scale=2)
        charts_ok = True
    except:
        pass
 
    # extra chart images
    scenario_chart_path = tmp.name + "_scenario.png"
    weekly_chart_path   = tmp.name + "_weekly.png"
    seasonality_bar_path = tmp.name + "_seasonality.png"
 
    try:
        # Scenario simulator chart
        fig_scenario = go.Figure()
        fig_scenario.add_trace(go.Scatter(x=future["date"], y=future["simulated_revenue"],
                                          name="Simulated Revenue", line=dict(color="#00C6FF", dash="dash")))
        fig_scenario.add_trace(go.Scatter(x=future["date"], y=future["simulated_profit"],
                                          name="Simulated Profit",
                                          line=dict(color="#2ECC71" if future["simulated_profit"].mean() >= 0 else "#EF4444")))
        fig_scenario.update_layout(template="plotly_white", title=f"Scenario Simulator ({discount}% Discount)",
                                   font={"color": "#1E293B"}, margin=dict(t=40, b=30))
        fig_scenario.write_image(scenario_chart_path, width=900, height=320, scale=2)
 
        # Weekly revenue summary chart (bar)
        weekly = trend.copy()
        weekly["week"] = weekly["date"].dt.to_period("W").astype(str)
        weekly_sum = weekly.groupby("week")["revenue"].sum().tail(12).reset_index()
        fig_weekly = go.Figure(go.Bar(
            x=weekly_sum["week"], y=weekly_sum["revenue"],
            marker_color="#0284C7", text=weekly_sum["revenue"].apply(lambda v: f"Rs.{v:,.0f}"),
            textposition="outside"
        ))
        fig_weekly.update_layout(template="plotly_white", title="Weekly Revenue Summary (Last 12 Weeks)",
                                 font={"color": "#1E293B"}, margin=dict(t=40, b=40))
        fig_weekly.write_image(weekly_chart_path, width=900, height=320, scale=2)
 
        # Day-wise seasonality bar chart
        if not seasonality.empty:
            day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
            s_ordered = seasonality.reindex([d for d in day_order if d in seasonality.index])
            bar_colors = ["#16A34A" if v == s_ordered.max() else ("#EF4444" if v == s_ordered.min() else "#0284C7")
                          for v in s_ordered.values]
            fig_season = go.Figure(go.Bar(
                x=s_ordered.index.tolist(), y=s_ordered.values,
                marker_color=bar_colors,
                text=[f"Rs.{v:,.0f}" for v in s_ordered.values],
                textposition="outside"
            ))
            fig_season.update_layout(template="plotly_white", title="Day-wise Average Revenue (Seasonality)",
                                     font={"color": "#1E293B"}, margin=dict(t=40, b=30))
            fig_season.write_image(seasonality_bar_path, width=900, height=300, scale=2)
    except:
        pass
 
    if charts_ok:
        elements.append(Paragraph("REVENUE FORECAST", style_section))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
        chart_w = PAGE_W - 1.2 * inch
        elements.append(Image(chart_path, width=chart_w, height=chart_w * 0.42))
        elements.append(Spacer(1, 12))
 
        elements.append(Paragraph("PROFIT vs REVENUE", style_section))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
        elements.append(Image(profit_chart_path, width=chart_w, height=chart_w * 0.38))
        elements.append(Spacer(1, 16))
    else:
        elements.append(Paragraph("Charts unavailable (kaleido not installed).", style_body))
 
    # ── SCENARIO SIMULATOR SECTION ──────────────────────────────────────────
    elements.append(Paragraph("SCENARIO SIMULATOR", style_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
    discount_note = Table([[Paragraph(
        f'<font color="#1E293B" size="9"><b>Applied Discount: {discount}%</b>  — Impact on Revenue and Profit shown below.</font>',
        style_body
    )]], colWidths=[PAGE_W - 1.2 * inch])
    discount_note.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("LINEABOVE",     (0, 0), (-1, 0), 2, BRAND_ACCENT),
    ]))
    elements.append(discount_note)
    elements.append(Spacer(1, 8))
 
    # Scenario table
    sc_data = [["Date", "Original Revenue", "Simulated Revenue", "Simulated Profit", "Impact"]]
    for _, row in future.iterrows():
        orig = row["predicted"]
        sim_rev = row["simulated_revenue"]
        sim_pft = row["simulated_profit"]
        impact = sim_rev - orig
        impact_color = "#EF4444" if impact < 0 else "#16A34A"
        sc_data.append([
            Paragraph(f'<font color="#1E293B">{row["date"].strftime("%d %b %Y")}</font>', style_body),
            Paragraph(f'<font color="#0284C7">Rs.{orig:,.0f}</font>', style_body),
            Paragraph(f'<font color="#D97706">Rs.{sim_rev:,.0f}</font>', style_body),
            Paragraph(f'<font color="{"#16A34A" if sim_pft >= 0 else "#EF4444"}"><b>Rs.{sim_pft:,.0f}</b></font>', style_body),
            Paragraph(f'<font color="{impact_color}">{impact:+,.0f}</font>', style_body),
        ])
    sc_table = Table(sc_data, colWidths=[85, 110, 110, 110, 85], repeatRows=1)
    sc_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING",    (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, BRAND_DARK),
    ]))
    elements.append(sc_table)
    elements.append(Spacer(1, 8))
 
    # Scenario totals row
    sc_total_rev = future["simulated_revenue"].sum()
    sc_total_pft = future["simulated_profit"].sum()
    revenue_delta = sc_total_rev - pred_total
    sc_totals = Table([[
        Paragraph('<font color="#64748B" size="8">TOTAL SIMULATED REVENUE</font>', style_body),
        Paragraph('<font color="#64748B" size="8">TOTAL SIMULATED PROFIT</font>', style_body),
        Paragraph('<font color="#64748B" size="8">REVENUE IMPACT</font>', style_body),
    ],[
        Paragraph(f'<font color="#D97706" size="13"><b>Rs.{sc_total_rev:,.0f}</b></font>', style_body),
        Paragraph(f'<font color="{"#16A34A" if sc_total_pft >= 0 else "#EF4444"}" size="13"><b>Rs.{sc_total_pft:,.0f}</b></font>', style_body),
        Paragraph(f'<font color="{"#EF4444" if revenue_delta < 0 else "#16A34A"}" size="13"><b>{revenue_delta:+,.0f}</b></font>', style_body),
    ]], colWidths=[(PAGE_W - 1.2*inch)/3]*3, rowHeights=[20, 36])
    sc_totals.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#EFF6FF")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEAFTER",     (0, 0), (1, -1), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, -1), (-1, -1), 2, BRAND_ACCENT),
    ]))
    elements.append(sc_totals)
    elements.append(Spacer(1, 8))
 
    if os.path.exists(scenario_chart_path):
        chart_w = PAGE_W - 1.2 * inch
        elements.append(Image(scenario_chart_path, width=chart_w, height=chart_w * 0.36))
    elements.append(Spacer(1, 20))
 
    # ── WEEKLY REVENUE SUMMARY ──────────────────────────────────────────────
    elements.append(Paragraph("WEEKLY REVENUE SUMMARY", style_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
    weekly = trend.copy()
    weekly["week"] = weekly["date"].dt.to_period("W").astype(str)
    weekly_sum = weekly.groupby("week")["revenue"].sum().tail(12).reset_index()
    weekly_sum["wow_change"] = weekly_sum["revenue"].pct_change() * 100
 
    wk_data = [["Week", "Revenue", "WoW Change"]]
    for _, row in weekly_sum.iterrows():
        wow = row["wow_change"]
        wow_str = f"{wow:+.1f}%" if not pd.isna(wow) else "—"
        wow_color = "#16A34A" if (not pd.isna(wow) and wow >= 0) else "#EF4444"
        wk_data.append([
            Paragraph(f'<font color="#1E293B">{row["week"]}</font>', style_body),
            Paragraph(f'<font color="#0284C7"><b>Rs.{row["revenue"]:,.0f}</b></font>', style_body),
            Paragraph(f'<font color="{wow_color}">{wow_str}</font>', style_body),
        ])
    wk_table = Table(wk_data, colWidths=[200, 150, 110], repeatRows=1)
    wk_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0), BRAND_DARK),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING",    (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, BRAND_DARK),
    ]))
    elements.append(wk_table)
    elements.append(Spacer(1, 8))
    if os.path.exists(weekly_chart_path):
        chart_w = PAGE_W - 1.2 * inch
        elements.append(Image(weekly_chart_path, width=chart_w, height=chart_w * 0.36))
    elements.append(Spacer(1, 20))
 
    # ── BUSINESS HEALTH METRICS ─────────────────────────────────────────────
    elements.append(Paragraph("BUSINESS HEALTH METRICS", style_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
    volatility = hist["actual"].std() / (hist["actual"].mean() + 1e-5) if "actual" in hist.columns else 0
    risk_level = "High" if volatility > 0.5 else ("Medium" if volatility > 0.25 else "Low")
    risk_color_hex = "#EF4444" if risk_level == "High" else ("#D97706" if risk_level == "Medium" else "#16A34A")
    avg_daily_rev = hist["actual"].mean() if "actual" in hist.columns else pred_total / max(days, 1)
    peak_day_val = hist["actual"].max() if "actual" in hist.columns else 0
    min_day_val  = hist["actual"].min() if "actual" in hist.columns else 0
    data_points   = len(hist)
 
    bh_inner = [
        [Paragraph('<font color="#64748B" size="8">VOLATILITY INDEX</font>', style_body),
         Paragraph('<font color="#64748B" size="8">RISK LEVEL</font>', style_body),
         Paragraph('<font color="#64748B" size="8">AVG DAILY REVENUE</font>', style_body),
         Paragraph('<font color="#64748B" size="8">DATA POINTS</font>', style_body)],
        [Paragraph(f'<font color="#D97706" size="14"><b>{volatility:.3f}</b></font>', style_body),
         Paragraph(f'<font color="{risk_color_hex}" size="14"><b>{risk_level}</b></font>', style_body),
         Paragraph(f'<font color="#0284C7" size="14"><b>Rs.{avg_daily_rev:,.0f}</b></font>', style_body),
         Paragraph(f'<font color="#1E293B" size="14"><b>{data_points}</b></font>', style_body)],
    ]
    bh_col = (PAGE_W - 1.2 * inch) / 4
    bh_table = Table(bh_inner, colWidths=[bh_col] * 4, rowHeights=[20, 36])
    bh_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), BRAND_CARD),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEAFTER",     (0, 0), (2, -1), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, -1), (-1, -1), 2, BRAND_ACCENT),
    ]))
    elements.append(bh_table)
    elements.append(Spacer(1, 8))
 
    bh_detail = Table([[
        Paragraph('<font color="#64748B" size="8">PEAK DAY REVENUE</font>', style_body),
        Paragraph('<font color="#64748B" size="8">LOWEST DAY REVENUE</font>', style_body),
        Paragraph('<font color="#64748B" size="8">BEST DAY OF WEEK</font>', style_body),
        Paragraph('<font color="#64748B" size="8">WORST DAY OF WEEK</font>', style_body),
    ],[
        Paragraph(f'<font color="#16A34A" size="13"><b>Rs.{peak_day_val:,.0f}</b></font>', style_body),
        Paragraph(f'<font color="#EF4444" size="13"><b>Rs.{min_day_val:,.0f}</b></font>', style_body),
        Paragraph(f'<font color="#0284C7" size="13"><b>{best_day}</b></font>', style_body),
        Paragraph(f'<font color="#EF4444" size="13"><b>{worst_day}</b></font>', style_body),
    ]], colWidths=[bh_col] * 4, rowHeights=[20, 36])
    bh_detail.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#E2E8F0")),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEAFTER",     (0, 0), (2, -1), 1, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 1, colors.HexColor("#CBD5E1")),
    ]))
    elements.append(bh_detail)
    elements.append(Spacer(1, 20))
 
    # ── MODEL COMPARISON TABLE (Auto mode) ─────────────────────────────────
    if model_type.startswith("Auto") and "score_df" in dir():
        elements.append(Paragraph("MODEL COMPARISON (AUTO MODE)", style_section))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
        mc_data = [["Rank", "Model", "MAPE Score", "Status"]]
        for rank, (_, row) in enumerate(score_df.iterrows(), 1):
            is_best = row["Model"] == best_model
            status_txt = "SELECTED" if is_best else "—"
            status_col = "#16A34A" if is_best else "#64748B"
            mape_col = "#16A34A" if rank == 1 else ("#D97706" if rank == 2 else "#EF4444")
            mc_data.append([
                Paragraph(f'<font color="#64748B">#{rank}</font>', style_body),
                Paragraph(f'<font color="{"#0284C7" if is_best else "#1E293B"}"><b>{row["Model"]}</b></font>', style_body),
                Paragraph(f'<font color="{mape_col}"><b>{row["MAPE"]:.2f}%</b></font>', style_body),
                Paragraph(f'<font color="{status_col}"><b>{status_txt}</b></font>', style_body),
            ])
        mc_table = Table(mc_data, colWidths=[50, 160, 120, 120], repeatRows=1)
        mc_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0), 9),
            ("TOPPADDING",    (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING",    (0, 1), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
            ("LINEBELOW",     (0, 0), (-1, 0), 2, BRAND_DARK),
        ]))
        elements.append(mc_table)
        elements.append(Spacer(1, 20))
 
    # ── FORECAST TABLE ─────────────────────────────────────────────────────
    elements.append(Paragraph("DETAILED FORECAST", style_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
    has_profit = "profit" in future.columns
    header = ["#", "Date", "Forecast Revenue", "Estimated Cost", "Est. Profit"] if has_profit else ["#", "Date", "Forecast Revenue"]
    table_data = [header]
 
    for i, (_, row) in enumerate(future.iterrows(), 1):
        rev = row["predicted"]
        cost_val = row.get("cost", rev * cost_pct / 100 + fixed_cost)
        profit_val = row.get("profit", rev - cost_val)
        profit_color_hex = "#2ECC71" if profit_val >= 0 else "#EF4444"
 
        if has_profit:
            table_data.append([
                Paragraph(f'<font color="#64748B">{i}</font>', style_body),
                Paragraph(f'<font color="#1E293B">{row["date"].strftime("%d %b %Y")}</font>', style_body),
                Paragraph(f'<font color="#0284C7"><b>Rs.{rev:,.0f}</b></font>', style_body),
                Paragraph(f'<font color="#D97706">Rs.{cost_val:,.0f}</font>', style_body),
                Paragraph(f'<font color="{profit_color_hex}"><b>Rs.{profit_val:,.0f}</b></font>', style_body),
            ])
        else:
            table_data.append([
                Paragraph(f'<font color="#64748B">{i}</font>', style_body),
                Paragraph(f'<font color="#1E293B">{row["date"].strftime("%d %b %Y")}</font>', style_body),
                Paragraph(f'<font color="#0284C7"><b>Rs.{rev:,.0f}</b></font>', style_body),
            ])
 
    if has_profit:
        col_widths = [30, 90, 120, 110, 110]
    else:
        col_widths = [30, 110, 150]
 
    forecast_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    forecast_table.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0), BRAND_ACCENT),
        ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 9),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        # Rows
        ("BACKGROUND",    (0, 1), (-1, -1), colors.white),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("TOPPADDING",    (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ("LINEBELOW",     (0, 0), (-1, 0), 2, BRAND_DARK),
    ]))
    elements.append(forecast_table)
    elements.append(Spacer(1, 20))
 
    # ── AI INSIGHT BLOCK ───────────────────────────────────────────────────
    elements.append(Paragraph("AI BUSINESS INSIGHTS", style_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
    if total_profit < 0:
        status_label = "LOSS DETECTED"
        status_color = BRAND_RED
        insight_lines = [
            "Business is operating at a loss. Immediate action required.",
            f"Category: {category_type}",
            "Recommendations: Cut 10-20% operational costs, pause low-ROI ad campaigns,",
            "reprice underperforming products, and remove loss-making SKUs.",
        ]
    elif growth is not None and growth < 0:
        status_label = "DECLINING DEMAND"
        status_color = BRAND_YELLOW
        insight_lines = [
            f"Sales are declining. Category: {category_type}",
            f"Best performing day: {best_day}. Focus promotions around this day.",
            "Recommendations: Retarget existing customers, refresh ad creatives,",
            "introduce discounts, and invest in SEO improvements.",
        ]
    elif profit_margin < 10:
        status_label = "LOW MARGIN WARNING"
        status_color = BRAND_YELLOW
        insight_lines = [
            f"Profit margins are below 10%. Category: {category_type}",
            f"Ad Efficiency Score: {ad_efficiency:.1f}",
            "Recommendations: Increase product pricing slightly, bundle products",
            "to increase AOV, and focus ads on high-value customer segments.",
        ]
    elif growth is not None and growth > 10:
        status_label = "STRONG GROWTH"
        status_color = BRAND_GREEN
        insight_lines = [
            f"Strong growth of {growth:.1f}% detected. Category: {category_type}",
            f"Best performing day: {best_day}.",
            "Recommendations: Scale ad spend, expand inventory proactively,",
            "secure supply chain early to avoid stockouts.",
        ]
    else:
        status_label = "STABLE PERFORMANCE"
        status_color = BRAND_ACCENT
        insight_lines = [
            f"Business is performing stably. Category: {category_type}",
            f"Best day: {best_day}  |  Weakest day: {worst_day}",
            "Recommendations: Run A/B tests on pricing and creatives,",
            "focus on customer retention and brand building.",
        ]
 
    # Status badge
    badge_data = [[Paragraph(
        f'<font color="white" size="11"><b>  {status_label}  </b></font>', style_body
    )]]
    badge = Table(badge_data)
    badge.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), status_color),
        ("TOPPADDING",    (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
    ]))
    elements.append(badge)
    elements.append(Spacer(1, 8))
 
    insight_block_data = [[
        Paragraph("<br/>".join(insight_lines), style_insight)
    ]]
    insight_block = Table(insight_block_data, colWidths=[PAGE_W - 1.2 * inch])
    insight_block.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
        ("TOPPADDING",    (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("LINEAFTER",     (0, 0), (0, -1), 3, status_color),
        ("LINEBELOW",     (0, -1), (-1, -1), 1, colors.HexColor("#E2E8F0")),
    ]))
    elements.append(insight_block)
    elements.append(Spacer(1, 20))
 
    # ── SEASONALITY TABLE ──────────────────────────────────────────────────
    if not seasonality.empty:
        elements.append(Paragraph("SEASONALITY ANALYSIS", style_section))
        elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
        day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        season_data = [["Day", "Avg Revenue", "Performance"]]
 
        max_rev = seasonality.max()
        for day in day_order:
            if day in seasonality.index:
                val = seasonality[day]
                pct = (val / max_rev) * 100
                bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
                bar_color = "#2ECC71" if pct >= 70 else ("#F59E0B" if pct >= 40 else "#EF4444")
                season_data.append([
                    Paragraph(f'<font color="#1E293B">{day}</font>', style_body),
                    Paragraph(f'<font color="#0284C7">Rs.{val:,.0f}</font>', style_body),
                    Paragraph(f'<font color="{bar_color}">{bar} {pct:.0f}%</font>', style_body),
                ])
 
        season_table = Table(season_data, colWidths=[120, 130, 210])
        season_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), BRAND_DARK),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.white),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",      (0, 0), (-1, 0), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#CBD5E1")),
        ]))
        elements.append(season_table)
        elements.append(Spacer(1, 8))
        if os.path.exists(seasonality_bar_path):
            chart_w_s = PAGE_W - 1.2 * inch
            elements.append(Image(seasonality_bar_path, width=chart_w_s, height=chart_w_s * 0.34))
        elements.append(Spacer(1, 20))
 
    # ── ANOMALY SUMMARY ────────────────────────────────────────────────────
    elements.append(Paragraph("ANOMALY DETECTION SUMMARY", style_section))
    elements.append(HRFlowable(width="100%", thickness=1, color=BRAND_CARD, spaceAfter=8))
 
    if not anomalies.empty:
        anom_intro = Paragraph(
            f'<font color="#EF4444"><b>{len(anomalies)} anomalies detected</b></font>'
            f'<font color="#CBD5E1"> in your historical sales data.</font>',
            style_body
        )
        elements.append(anom_intro)
        elements.append(Spacer(1, 6))
 
        anom_data = [["Date", "Revenue"]]
        for _, row in anomalies.head(10).iterrows():
            anom_data.append([
                Paragraph(f'<font color="#1E293B">{pd.to_datetime(row["date"]).strftime("%d %b %Y")}</font>', style_body),
                Paragraph(f'<font color="#DC2626">Rs.{row["revenue"]:,.0f}</font>', style_body),
            ])
        anom_table = Table(anom_data, colWidths=[180, 180])
        anom_table.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, 0), colors.HexColor("#FEE2E2")),
            ("TEXTCOLOR",     (0, 0), (-1, 0), colors.HexColor("#991B1B")),
            ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FFF5F5")]),
            ("TOPPADDING",    (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#FECACA")),
        ]))
        elements.append(anom_table)
    else:
        elements.append(Paragraph(
            '<font color="#2ECC71"><b>No anomalies detected.</b></font>'
            '<font color="#CBD5E1"> Your sales data looks clean and consistent.</font>',
            style_body
        ))
 
    elements.append(Spacer(1, 30))
 
    # ── SIGN-OFF ────────────────────────────────────────────────────────────
    signoff_data = [[
        Paragraph(
            f'<font color="#94A3B8" size="8">This report was automatically generated by <b>Forecastly</b> '
            f'AI Business Intelligence Engine on {datetime.now().strftime("%d %b %Y at %H:%M")}. '
            f'Forecasts are probabilistic estimates and should be used as guidance only.</font>',
            style_footer
        )
    ]]
    signoff = Table(signoff_data, colWidths=[PAGE_W - 1.2 * inch])
    signoff.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 14),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 14),
        ("LINEABOVE",     (0, 0), (-1, 0), 1, BRAND_ACCENT),
    ]))
    elements.append(signoff)
 
    # ── BUILD ──────────────────────────────────────────────────────────────
    doc.build(elements, onFirstPage=draw_page, onLaterPages=draw_page)
 
    # Cleanup chart images
    for p in [chart_path, profit_chart_path, scenario_chart_path, weekly_chart_path, seasonality_bar_path]:
        try:
            os.remove(p)
        except:
            pass
 
    return tmp.name
 
 
pdf_file = generate_pdf()
 
with open(pdf_file, "rb") as f:
    st.download_button(
        "📄 Download Professional Report",
        f,
        file_name=f"forecastly_report_{datetime.now().strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
 
st.caption("🚀 Forecastly • AI Business Intelligence")