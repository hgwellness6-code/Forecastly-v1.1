"""
Forecastly Data Store
Uses Streamlit session_state for cloud-compatible persistence.
"""
import pandas as pd
import numpy as np
import streamlit as st

INVOICE_TYPES = {
    "fba_fees":    {"label": "FBA Fees",          "icon": "📦", "color": "#E8452C"},
    "shipping":    {"label": "Shipping / Courier", "icon": "🚚", "color": "#F5A623"},
    "storage":     {"label": "Storage Fees",       "icon": "🏭", "color": "#7B61FF"},
    "advertising": {"label": "Advertising (PPC)",  "icon": "📣", "color": "#00C6FF"},
    "returns":     {"label": "Returns / Refunds",  "icon": "↩️",  "color": "#FF6B6B"},
    "sales":       {"label": "Sales Revenue",      "icon": "💰", "color": "#2ECC71"},
}

STORE_KEY = "forecastly_invoices"

def _get_store() -> dict:
    if STORE_KEY not in st.session_state:
        st.session_state[STORE_KEY] = {}
    return st.session_state[STORE_KEY]


def save_invoice(invoice_type: str, df: pd.DataFrame):
    """Save invoice data to session state."""
    store = _get_store()
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    for col in df.columns:
        if "date" in col and col != "date":
            df = df.rename(columns={col: "date"})
            break

    if "date" not in df.columns:
        df["date"] = pd.Timestamp.today().date()

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["invoice_type"] = invoice_type

    if invoice_type in store and store[invoice_type] is not None:
        existing = store[invoice_type]
        df = pd.concat([existing, df], ignore_index=True).drop_duplicates()

    store[invoice_type] = df


def load_invoice(invoice_type: str) -> pd.DataFrame | None:
    store = _get_store()
    return store.get(invoice_type, None)


def load_all() -> dict:
    store = _get_store()
    return {k: v for k, v in store.items() if v is not None and not v.empty}


def clear_invoice(invoice_type: str):
    store = _get_store()
    if invoice_type in store:
        del store[invoice_type]


def get_summary() -> dict:
    summary = {}
    for itype in INVOICE_TYPES:
        df = load_invoice(itype)
        if df is not None and not df.empty:
            summary[itype] = {
                "rows": len(df),
                "uploaded": True,
                "min_date": str(df["date"].min().date()) if "date" in df.columns else "—",
                "max_date": str(df["date"].max().date()) if "date" in df.columns else "—",
            }
        else:
            summary[itype] = {"rows": 0, "uploaded": False}
    return summary
