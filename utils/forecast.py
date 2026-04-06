"""
Forecastly Forecast Engine
Wraps multiple forecasting models.
"""
import pandas as pd
import numpy as np


def _make_future_df(trend: pd.DataFrame, days: int, predicted: np.ndarray) -> pd.DataFrame:
    """Helper: build a combined historical + future DataFrame."""
    trend = trend.copy()
    trend["date"] = pd.to_datetime(trend["date"])
    trend = trend.sort_values("date")

    hist_len = len(trend)
    hist_pred = predicted[:hist_len] if len(predicted) >= hist_len else np.full(hist_len, np.nan)

    last_date = trend["date"].iloc[-1]
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=days)

    hist_df = trend[["date", "revenue"]].copy()
    hist_df.columns = ["date", "actual"]
    hist_df["predicted"] = hist_pred
    hist_df["is_future"] = False

    future_pred = predicted[hist_len:hist_len + days] if len(predicted) > hist_len else np.full(days, np.nan)
    fut_df = pd.DataFrame({"date": future_dates, "actual": np.nan, "predicted": future_pred, "is_future": True})

    return pd.concat([hist_df, fut_df], ignore_index=True)


def run_forecast(trend: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """Scikit-Learn linear regression forecast."""
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler

        trend = trend.copy()
        trend["date"] = pd.to_datetime(trend["date"])
        trend = trend.sort_values("date")
        y = trend["revenue"].fillna(0).values
        X = np.arange(len(y)).reshape(-1, 1)

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = Ridge()
        model.fit(X_scaled, y)

        X_full = np.arange(len(y) + days).reshape(-1, 1)
        X_full_scaled = scaler.transform(X_full)
        predicted = model.predict(X_full_scaled)

        return _make_future_df(trend, days, predicted)
    except Exception:
        return pd.DataFrame()


def run_prophet_forecast(trend: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """Facebook Prophet forecast."""
    try:
        from prophet import Prophet

        trend = trend.copy()
        trend["date"] = pd.to_datetime(trend["date"])
        df_prophet = trend[["date", "revenue"]].rename(columns={"date": "ds", "revenue": "y"})
        df_prophet["y"] = df_prophet["y"].fillna(0)

        model = Prophet(daily_seasonality=False, weekly_seasonality=True)
        model.fit(df_prophet)

        future = model.make_future_dataframe(periods=days)
        forecast = model.predict(future)

        hist_len = len(trend)
        predicted_all = forecast["yhat"].values
        result = _make_future_df(trend, days, predicted_all)

        # Add confidence intervals
        result["lower"] = np.nan
        result["upper"] = np.nan
        fut_mask = result["is_future"]
        result.loc[fut_mask, "lower"] = forecast["yhat_lower"].values[-days:]
        result.loc[fut_mask, "upper"] = forecast["yhat_upper"].values[-days:]

        return result
    except Exception:
        return run_forecast(trend, days)


def run_xgb_forecast(trend: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """XGBoost forecast with lag features."""
    try:
        import xgboost as xgb

        trend = trend.copy()
        trend["date"] = pd.to_datetime(trend["date"])
        trend = trend.sort_values("date")
        y = trend["revenue"].fillna(0).values

        def make_features(arr):
            rows = []
            for i in range(7, len(arr)):
                rows.append([arr[i-1], arr[i-2], arr[i-3], arr[i-7], np.mean(arr[i-7:i])])
            return np.array(rows)

        if len(y) < 8:
            return run_forecast(trend, days)

        X_train = make_features(y)
        y_train = y[7:]

        model = xgb.XGBRegressor(n_estimators=100, max_depth=3, learning_rate=0.1, verbosity=0)
        model.fit(X_train, y_train)

        history = list(y)
        future_preds = []
        for _ in range(days):
            feat = np.array([[history[-1], history[-2], history[-3], history[-7], np.mean(history[-7:])]])
            pred = model.predict(feat)[0]
            future_preds.append(pred)
            history.append(pred)

        hist_preds = model.predict(X_train)
        predicted_hist = np.concatenate([np.full(7, np.nan), hist_preds])
        predicted_all = np.concatenate([predicted_hist, future_preds])

        return _make_future_df(trend, days, predicted_all)
    except Exception:
        return run_forecast(trend, days)


def run_arima_forecast(trend: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """ARIMA forecast using statsmodels."""
    try:
        from statsmodels.tsa.arima.model import ARIMA

        trend = trend.copy()
        trend["date"] = pd.to_datetime(trend["date"])
        trend = trend.sort_values("date")
        y = trend["revenue"].fillna(0).values

        if len(y) < 10:
            return run_forecast(trend, days)

        model = ARIMA(y, order=(2, 1, 2))
        result = model.fit()

        hist_pred = result.fittedvalues
        future_pred = result.forecast(steps=days)
        predicted_all = np.concatenate([hist_pred, future_pred])

        return _make_future_df(trend, days, predicted_all)
    except Exception:
        return run_forecast(trend, days)


def run_neuralprophet_forecast(trend: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """NeuralProphet forecast (falls back to Prophet if unavailable)."""
    try:
        from neuralprophet import NeuralProphet

        trend = trend.copy()
        trend["date"] = pd.to_datetime(trend["date"])
        df_np = trend[["date", "revenue"]].rename(columns={"date": "ds", "revenue": "y"})
        df_np["y"] = df_np["y"].fillna(0)

        model = NeuralProphet(epochs=50, batch_size=16, learning_rate=0.01)
        model.fit(df_np, freq="D")

        future = model.make_future_dataframe(df_np, periods=days)
        forecast = model.predict(future)

        predicted_all = forecast["yhat1"].values
        return _make_future_df(trend, days, predicted_all)
    except Exception:
        return run_prophet_forecast(trend, days)


def run_pycaret_forecast(trend: pd.DataFrame, days: int = 14) -> pd.DataFrame:
    """PyCaret AutoML forecast (falls back to XGBoost if unavailable)."""
    try:
        from pycaret.time_series import setup, compare_models, predict_model

        trend = trend.copy()
        trend["date"] = pd.to_datetime(trend["date"])
        trend = trend.set_index("date")["revenue"].fillna(0)

        setup(trend, fh=days, session_id=42, verbose=False)
        best = compare_models(verbose=False)
        forecast = predict_model(best)

        predicted_future = forecast["y_pred"].values
        trend_reset = trend.reset_index()
        trend_reset.columns = ["date", "revenue"]

        hist_df = trend_reset.copy()
        hist_df["actual"] = hist_df["revenue"]
        hist_df["predicted"] = hist_df["revenue"]
        hist_df["is_future"] = False

        last_date = trend_reset["date"].iloc[-1]
        future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=days)
        fut_df = pd.DataFrame({"date": future_dates, "actual": np.nan,
                                "predicted": predicted_future, "is_future": True})

        return pd.concat([hist_df[["date", "actual", "predicted", "is_future"]], fut_df], ignore_index=True)
    except Exception:
        return run_xgb_forecast(trend, days)


def detect_anomalies(trend: pd.DataFrame) -> pd.DataFrame:
    """Flag anomalous revenue days using IQR method."""
    trend = trend.copy()
    if "revenue" not in trend.columns or trend.empty:
        trend["anomaly"] = 0
        return trend

    q1 = trend["revenue"].quantile(0.25)
    q3 = trend["revenue"].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr

    trend["anomaly"] = ((trend["revenue"] < lower) | (trend["revenue"] > upper)).astype(int)
    return trend


def calculate_mape(actual: pd.Series, predicted: pd.Series) -> float:
    """Mean Absolute Percentage Error."""
    actual = pd.to_numeric(actual, errors="coerce").fillna(0)
    predicted = pd.to_numeric(predicted, errors="coerce").fillna(0)
    mask = actual != 0
    if mask.sum() == 0:
        return 999.0
    return float(np.mean(np.abs((actual[mask] - predicted[mask]) / actual[mask])) * 100)
