"""
Forecastly File Parser
Handles CSV, Excel, and PDF invoice parsing.
"""
import pandas as pd
import io


def parse_file(uploaded_file, itype: str) -> pd.DataFrame:
    """Parse an uploaded file (CSV, Excel, PDF) into a DataFrame."""
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
            headers = rows[0]
            data = rows[1:]
            return pd.DataFrame(data, columns=headers)
        except Exception as e:
            raise ValueError(f"PDF parsing failed: {e}")

    else:
        raise ValueError(f"Unsupported file type: {uploaded_file.name}")


def detect_amount_column(df: pd.DataFrame) -> str | None:
    """Detect the most likely amount/value column."""
    priority_keywords = [
        "amount", "total", "value", "price", "revenue", "sales",
        "fee", "cost", "spend", "charge", "income", "net", "gross",
        "settlement", "payment", "refund", "credit", "debit",
    ]
    cols_lower = {c.lower(): c for c in df.columns}

    for keyword in priority_keywords:
        for col_lower, col_original in cols_lower.items():
            if keyword in col_lower:
                # Make sure it has numeric data
                try:
                    s = df[col_original].astype(str).str.replace(",", "").str.replace("₹", "").str.strip()
                    numeric = pd.to_numeric(s, errors="coerce")
                    if numeric.notna().sum() > 0:
                        return col_original
                except Exception:
                    continue

    # Fallback: first numeric column
    for col in df.columns:
        try:
            s = df[col].astype(str).str.replace(",", "").str.replace("₹", "").str.strip()
            numeric = pd.to_numeric(s, errors="coerce")
            if numeric.notna().mean() > 0.5:
                return col
        except Exception:
            continue

    return None


def detect_sku_column(df: pd.DataFrame) -> str | None:
    """Detect the most likely SKU / ASIN column."""
    keywords = ["sku", "asin", "product", "item", "listing", "fnsku", "msku"]
    cols_lower = {c.lower(): c for c in df.columns}

    for keyword in keywords:
        for col_lower, col_original in cols_lower.items():
            if keyword in col_lower:
                return col_original

    return None
