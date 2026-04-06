"""
Forecastly File Parser — root-level module (no utils/ folder needed)
"""
import pandas as pd


def parse_file(uploaded_file, itype: str) -> pd.DataFrame:
    """Parse CSV, Excel, or PDF into a DataFrame."""
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
        try:
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
        except Exception as e:
            raise ValueError(f"PDF parsing failed: {e}")

    raise ValueError(f"Unsupported file type: {uploaded_file.name}")


def detect_amount_column(df: pd.DataFrame) -> str | None:
    """Find the most likely monetary amount column."""
    priority = ["amount", "total", "value", "price", "revenue", "sales",
                "fee", "cost", "spend", "charge", "net", "gross",
                "settlement", "payment", "refund", "credit", "debit"]
    cols_lower = {c.lower(): c for c in df.columns}
    for kw in priority:
        for cl, co in cols_lower.items():
            if kw in cl:
                try:
                    s = df[co].astype(str).str.replace(",", "").str.replace("₹", "").str.strip()
                    if pd.to_numeric(s, errors="coerce").notna().sum() > 0:
                        return co
                except Exception:
                    continue
    # fallback: first mostly-numeric column
    for col in df.columns:
        try:
            s = df[col].astype(str).str.replace(",", "").str.replace("₹", "").str.strip()
            if pd.to_numeric(s, errors="coerce").notna().mean() > 0.5:
                return col
        except Exception:
            continue
    return None


def detect_sku_column(df: pd.DataFrame) -> str | None:
    """Find the most likely SKU / ASIN column."""
    keywords = ["sku", "asin", "product", "item", "listing", "fnsku", "msku"]
    cols_lower = {c.lower(): c for c in df.columns}
    for kw in keywords:
        for cl, co in cols_lower.items():
            if kw in cl:
                return co
    return None
