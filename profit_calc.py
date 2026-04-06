"""
Forecastly Profit Calculator
Merges all invoice types into a unified P&L view per SKU / per date.
"""
import pandas as pd
import numpy as np
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from store import load_all, INVOICE_TYPES
from parser_utils import detect_amount_column, detect_sku_column

COST_TYPES    = ["fba_fees", "shipping", "storage", "advertising", "returns"]
REVENUE_TYPES = ["sales"]


def _extract_amount(df: pd.DataFrame) -> pd.Series:
    col = detect_amount_column(df)
    if col is None:
        return pd.Series(dtype=float)
    s = df[col].astype(str).str.replace(",", "").str.replace("₹", "").str.strip()
    return pd.to_numeric(s, errors="coerce").fillna(0)


def _extract_sku(df: pd.DataFrame) -> pd.Series:
    col = detect_sku_column(df)
    if col:
        return df[col].astype(str).str.strip()
    return pd.Series(["UNKNOWN"] * len(df))


def build_pnl(date_start=None, date_end=None) -> pd.DataFrame:
    data = load_all()
    if not data:
        return pd.DataFrame()

    records = []
    for itype, df in data.items():
        if df is None or df.empty:
            continue
        if "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"], errors="coerce")
            if date_start:
                df = df[df["date"] >= pd.to_datetime(date_start)]
            if date_end:
                df = df[df["date"] <= pd.to_datetime(date_end)]

        amounts = _extract_amount(df)
        skus    = _extract_sku(df)

        for i, (amt, sku) in enumerate(zip(amounts, skus)):
            records.append({
                "sku":          sku,
                "invoice_type": itype,
                "amount":       amt,
                "date":         df["date"].iloc[i] if "date" in df.columns else pd.NaT,
            })

    if not records:
        return pd.DataFrame()

    long = pd.DataFrame(records)
    pnl  = long.groupby(["sku", "invoice_type"])["amount"].sum().unstack(fill_value=0)

    for col in COST_TYPES + REVENUE_TYPES:
        if col not in pnl.columns:
            pnl[col] = 0.0

    pnl = pnl.reset_index()
    pnl["revenue"]    = pnl.get("sales", 0)
    pnl["total_cost"] = (pnl.get("fba_fees", 0) + pnl.get("shipping", 0)
                         + pnl.get("storage", 0) + pnl.get("advertising", 0)
                         + pnl.get("returns", 0))
    pnl["profit"]     = pnl["revenue"] - pnl["total_cost"]
    pnl["margin_pct"] = np.where(
        pnl["revenue"] != 0,
        (pnl["profit"] / pnl["revenue"] * 100).round(1), 0
    )
    return pnl.sort_values("profit", ascending=False)


def build_daily_trend(date_start=None, date_end=None) -> pd.DataFrame:
    data = load_all()
    if not data:
        return pd.DataFrame()

    records = []
    for itype, df in data.items():
        if df is None or df.empty or "date" not in df.columns:
            continue
        df = df.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        if date_start:
            df = df[df["date"] >= pd.to_datetime(date_start)]
        if date_end:
            df = df[df["date"] <= pd.to_datetime(date_end)]

        col = detect_amount_column(df)
        if col:
            s = df[col].astype(str).str.replace(",", "").str.replace("₹", "")
            df["amount"]       = pd.to_numeric(s, errors="coerce").fillna(0)
            df["invoice_type"] = itype
            records.append(df[["date", "invoice_type", "amount"]])

    if not records:
        return pd.DataFrame()

    long = pd.concat(records, ignore_index=True)
    long["date"] = long["date"].dt.date

    pivot = long.groupby(["date", "invoice_type"])["amount"].sum().unstack(fill_value=0)
    for col in COST_TYPES + REVENUE_TYPES:
        if col not in pivot.columns:
            pivot[col] = 0.0

    pivot = pivot.reset_index()
    pivot["revenue"]    = pivot.get("sales", 0)
    pivot["total_cost"] = (pivot.get("fba_fees", 0) + pivot.get("shipping", 0)
                           + pivot.get("storage", 0) + pivot.get("advertising", 0)
                           + pivot.get("returns", 0))
    pivot["profit"] = pivot["revenue"] - pivot["total_cost"]
    return pivot.sort_values("date")


def get_totals(date_start=None, date_end=None) -> dict:
    trend = build_daily_trend(date_start, date_end)
    if trend.empty:
        return {k: 0 for k in ["revenue", "fba_fees", "shipping", "storage",
                                "advertising", "returns", "total_cost", "profit", "margin_pct"]}
    rev    = trend["revenue"].sum()
    cost   = trend["total_cost"].sum()
    prof   = trend["profit"].sum()
    margin = round(prof / rev * 100, 1) if rev else 0
    return {
        "revenue":     rev,
        "fba_fees":    trend.get("fba_fees",    pd.Series([0])).sum(),
        "shipping":    trend.get("shipping",    pd.Series([0])).sum(),
        "storage":     trend.get("storage",     pd.Series([0])).sum(),
        "advertising": trend.get("advertising", pd.Series([0])).sum(),
        "returns":     trend.get("returns",     pd.Series([0])).sum(),
        "total_cost":  cost,
        "profit":      prof,
        "margin_pct":  margin,
    }
