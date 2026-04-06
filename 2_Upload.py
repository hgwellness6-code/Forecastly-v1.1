import streamlit as st
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import INVOICE_TYPES, save_invoice, load_invoice, clear_invoice
from parser_utils import parse_file, detect_amount_column, detect_sku_column
import pandas as pd


def detect_invoice_type(filename: str, df: pd.DataFrame) -> str | None:
    name_lower = filename.lower()
    keyword_map = {
        "settlement":   "settlement",
        "advertising":  "advertising",
        "ads":          "advertising",
        "sponsored":    "advertising",
        "return":       "returns",
        "refund":       "returns",
        "removal":      "removals",
        "reimburs":     "reimbursements",
        "storage":      "storage",
        "fba":          "fba_fees",
        "fee":          "fba_fees",
        "subscription": "subscription",
        "inventory":    "inventory",
        "order":        "orders",
        "sale":         "orders",
        "tax":          "tax",
        "shipping":     "shipping",
    }
    for keyword, itype in keyword_map.items():
        if keyword in name_lower and itype in INVOICE_TYPES:
            return itype

    cols_lower = [c.lower() for c in df.columns]
    col_str = " ".join(cols_lower)
    col_hints = {
        "settlement":     ["settlement", "transaction type", "marketplace"],
        "advertising":    ["campaign", "impressions", "clicks", "spend", "acos"],
        "returns":        ["return", "refund", "reason", "disposition"],
        "removals":       ["removal", "shipment", "disposition", "requested date"],
        "reimbursements": ["reimbursement", "case", "reason", "approval date"],
        "storage":        ["storage", "asin", "volume", "month of charge"],
        "fba_fees":       ["fee", "fba", "fulfilment", "per unit"],
        "orders":         ["order id", "order date", "quantity", "item price"],
        "tax":            ["tax", "taxable", "jurisdiction"],
    }
    for itype, hints in col_hints.items():
        if itype in INVOICE_TYPES and any(h in col_str for h in hints):
            return itype
    return None


st.markdown("# 📤 Upload Invoices")
st.markdown("""
Upload **each Amazon invoice type separately**. Supported formats: **CSV, Excel (.xlsx), PDF**.  
Forecastly will **auto-detect** the invoice type and merge everything into your P&L.
""")

uploaded = st.file_uploader(
    "Drop your invoice file here",
    type=["csv", "xlsx", "xls", "pdf"],
    key="uploader_auto",
)

if uploaded:
    with st.spinner("Parsing file…"):
        try:
            df_raw = parse_file(uploaded, list(INVOICE_TYPES.keys())[0])
            detected_itype = detect_invoice_type(uploaded.name, df_raw)

            if detected_itype:
                st.success(f"🔍 Auto-detected: **{INVOICE_TYPES[detected_itype]['icon']} {INVOICE_TYPES[detected_itype]['label']}**")
            else:
                st.warning("⚠️ Could not auto-detect invoice type. Please select manually.")

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
                st.success(f"✅ {info['label']} saved! Go to Dashboard to see updated P&L.")
                st.balloons()

        except Exception as e:
            st.error(f"❌ Failed to parse file: {e}")

st.divider()
st.markdown("### 🗂 Manage Existing Invoice Data")

for t, tinfo in INVOICE_TYPES.items():
    existing = load_invoice(t)
    with st.expander(f"{tinfo['icon']} {tinfo['label']} — {'✅ ' + str(len(existing)) + ' rows' if existing is not None else '⬜ Not uploaded'}"):
        if existing is not None:
            st.dataframe(existing.head(5), use_container_width=True)
            if st.button(f"🗑 Clear {tinfo['label']} data", key=f"clear_{t}"):
                clear_invoice(t)
                st.warning(f"{tinfo['label']} data cleared.")
                st.rerun()
        else:
            st.caption("No data uploaded yet.")
