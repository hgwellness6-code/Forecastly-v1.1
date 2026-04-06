import streamlit as st
import pandas as pd
import sys, os

# ── Inline store (avoids cross-file import issues on Streamlit Cloud) ─────────
INVOICE_TYPES = {
    "fba_fees":    {"label": "FBA Fees",          "icon": "📦", "color": "#E8452C"},
    "shipping":    {"label": "Shipping / Courier", "icon": "🚚", "color": "#F5A623"},
    "storage":     {"label": "Storage Fees",       "icon": "🏭", "color": "#7B61FF"},
    "advertising": {"label": "Advertising (PPC)",  "icon": "📣", "color": "#00C6FF"},
    "returns":     {"label": "Returns / Refunds",  "icon": "↩️",  "color": "#FF6B6B"},
    "sales":       {"label": "Sales Revenue",      "icon": "💰", "color": "#2ECC71"},
}
STORE_KEY = "forecastly_invoices"

def _get_store():
    if STORE_KEY not in st.session_state:
        st.session_state[STORE_KEY] = {}
    return st.session_state[STORE_KEY]

def save_invoice(invoice_type, df):
    store = _get_store()
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    for col in df.columns:
        if "date" in col and col != "date":
            df = df.rename(columns={col: "date"}); break
    if "date" not in df.columns:
        df["date"] = pd.Timestamp.today().date()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["invoice_type"] = invoice_type
    if invoice_type in store and store[invoice_type] is not None:
        df = pd.concat([store[invoice_type], df], ignore_index=True).drop_duplicates()
    store[invoice_type] = df

def load_invoice(invoice_type):
    return _get_store().get(invoice_type, None)

def clear_invoice(invoice_type):
    store = _get_store()
    if invoice_type in store:
        del store[invoice_type]

# ── Inline parser ─────────────────────────────────────────────────────────────
def parse_file(uploaded_file, itype):
    uploaded_file.seek(0)
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        try:
            return pd.read_csv(uploaded_file, encoding="utf-8")
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding="latin-1")
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(uploaded_file)
    elif name.endswith(".pdf"):
        import pdfplumber
        rows = []
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    rows.extend(table)
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows[1:], columns=rows[0])
    raise ValueError(f"Unsupported file type: {uploaded_file.name}")

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
    for col in df.columns:
        try:
            s = df[col].astype(str).str.replace(",","").str.replace("₹","").str.strip()
            if pd.to_numeric(s, errors="coerce").notna().mean() > 0.5:
                return col
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

def detect_invoice_type(filename, df):
    name_lower = filename.lower()
    keyword_map = {
        "settlement":"settlement","advertising":"advertising","ads":"advertising",
        "sponsored":"advertising","return":"returns","refund":"returns",
        "removal":"removals","reimburs":"reimbursements","storage":"storage",
        "fba":"fba_fees","fee":"fba_fees","order":"orders","sale":"orders",
        "tax":"tax","shipping":"shipping",
    }
    for kw, itype in keyword_map.items():
        if kw in name_lower and itype in INVOICE_TYPES:
            return itype
    col_str = " ".join(c.lower() for c in df.columns)
    col_hints = {
        "advertising": ["campaign","impressions","clicks","spend","acos"],
        "returns":     ["return","refund","disposition"],
        "storage":     ["storage","volume","month of charge"],
        "fba_fees":    ["fba","fulfilment","per unit"],
        "orders":      ["order id","order date","quantity","item price"],
    }
    for itype, hints in col_hints.items():
        if itype in INVOICE_TYPES and any(h in col_str for h in hints):
            return itype
    return None

# ── Page UI ───────────────────────────────────────────────────────────────────
st.markdown("# 📤 Upload Invoices")
st.markdown("Upload **each Amazon invoice type separately**. Supported formats: **CSV, Excel (.xlsx), PDF**.")

uploaded = st.file_uploader("Drop your invoice file here", type=["csv","xlsx","xls","pdf"], key="uploader_auto")

if uploaded:
    with st.spinner("Parsing file…"):
        try:
            df_raw = parse_file(uploaded, list(INVOICE_TYPES.keys())[0])
            detected_itype = detect_invoice_type(uploaded.name, df_raw)

            if detected_itype:
                st.success(f"🔍 Auto-detected: **{INVOICE_TYPES[detected_itype]['icon']} {INVOICE_TYPES[detected_itype]['label']}**")
            else:
                st.warning("⚠️ Could not auto-detect. Please select manually.")

            itype = st.selectbox(
                "Confirm or change invoice type",
                options=list(INVOICE_TYPES.keys()),
                index=list(INVOICE_TYPES.keys()).index(detected_itype) if detected_itype else 0,
                format_func=lambda k: f"{INVOICE_TYPES[k]['icon']}  {INVOICE_TYPES[k]['label']}",
            )
            info = INVOICE_TYPES[itype]
            df = parse_file(uploaded, itype) if itype != detected_itype else df_raw
            st.success(f"✅ Parsed {len(df)} rows from **{uploaded.name}**")

            amt_col = detect_amount_column(df)
            sku_col = detect_sku_column(df)
            col1, col2 = st.columns(2)
            col1.info(f"💰 Amount column: **{amt_col or 'None'}**")
            col2.info(f"📦 SKU column: **{sku_col or 'None'}**")

            st.markdown("#### Preview (first 10 rows)")
            st.dataframe(df.head(10), use_container_width=True)

            with st.expander("⚙️ Override column mapping (optional)"):
                all_cols = ["(auto-detect)"] + list(df.columns)
                man_amt  = st.selectbox("Amount column",     all_cols, key="man_amt")
                man_sku  = st.selectbox("SKU / ASIN column", all_cols, key="man_sku")
                man_date = st.selectbox("Date column",       all_cols, key="man_date")
                if man_amt  != "(auto-detect)": df = df.rename(columns={man_amt:  "amount"})
                if man_sku  != "(auto-detect)": df = df.rename(columns={man_sku:  "sku"})
                if man_date != "(auto-detect)": df = df.rename(columns={man_date: "date"})

            if st.button(f"💾 Save {info['label']} to Forecastly", type="primary"):
                save_invoice(itype, df)
                st.success(f"✅ {info['label']} saved!")
                st.balloons()
        except Exception as e:
            st.error(f"❌ Failed to parse file: {e}")

st.divider()
st.markdown("### 🗂 Manage Existing Invoice Data")
for t, tinfo in INVOICE_TYPES.items():
    existing = load_invoice(t)
    label = f"{'✅ ' + str(len(existing)) + ' rows' if existing is not None else '⬜ Not uploaded'}"
    with st.expander(f"{tinfo['icon']} {tinfo['label']} — {label}"):
        if existing is not None:
            st.dataframe(existing.head(5), use_container_width=True)
            if st.button(f"🗑 Clear {tinfo['label']}", key=f"clear_{t}"):
                clear_invoice(t)
                st.rerun()
        else:
            st.caption("No data uploaded yet.")
