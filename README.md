# 🔥 Forecastly — Amazon Invoice Intelligence

AI-powered Amazon P&L dashboard with sales forecasting.

## Features
- Upload FBA Fees, Shipping, Storage, Advertising, Returns & Sales invoices
- Auto-detect amount and SKU columns
- Unified P&L dashboard per SKU
- 14-day sales forecast (Prophet, XGBoost, ARIMA, Scikit-Learn)
- PDF report export

## Deploy on Streamlit Cloud
1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo → set main file as `app.py`
4. Click Deploy

## Run Locally
```bash
pip install -r requirements.txt
streamlit run app.py
```
