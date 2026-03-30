from pathlib import Path
from threading import Lock

import pandas as pd
from flask import Flask, Response, render_template, request


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / "logs_dataset.csv"
ANOMALY_PATH = BASE_DIR / "trained_models" / "anomaly_scores.csv"


app = Flask(__name__)
request_lock = Lock()
request_metrics = {}
dataset_gauges = {
    "rows": 0,
    "anomalies": 0,
    "providers": 0,
    "event_ids": 0,
}


def load_dataframe():
    source = None

    if ANOMALY_PATH.exists():
        df = pd.read_csv(ANOMALY_PATH)
        source = "anomaly"
    elif DATASET_PATH.exists():
        df = pd.read_csv(DATASET_PATH)
        source = "logs"
    else:
        return None, None

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    return df, source


def update_dataset_gauges(df):
    with request_lock:
        if df is None:
            dataset_gauges["rows"] = 0
            dataset_gauges["anomalies"] = 0
            dataset_gauges["providers"] = 0
            dataset_gauges["event_ids"] = 0
            return

        metrics = build_metrics(df)
        dataset_gauges["rows"] = int(str(metrics["total_rows"]).replace(",", ""))
        dataset_gauges["anomalies"] = metrics["anomalies"]
        dataset_gauges["providers"] = metrics["providers"]
        dataset_gauges["event_ids"] = metrics["event_ids"]


def update_request_counter():
    endpoint = request.endpoint or request.path
    key = (endpoint, request.method)
    with request_lock:
        request_metrics[key] = request_metrics.get(key, 0) + 1


def build_metrics_payload():
    lines = [
        "# HELP app_loaded_rows_total Number of rows loaded from the dataset",
        "# TYPE app_loaded_rows_total gauge",
        f"app_loaded_rows_total {dataset_gauges['rows']}",
        "# HELP app_anomaly_rows_total Number of anomaly rows loaded from the dataset",
        "# TYPE app_anomaly_rows_total gauge",
        f"app_anomaly_rows_total {dataset_gauges['anomalies']}",
        "# HELP app_loaded_providers_total Number of unique providers in the dataset",
        "# TYPE app_loaded_providers_total gauge",
        f"app_loaded_providers_total {dataset_gauges['providers']}",
        "# HELP app_loaded_event_ids_total Number of unique event IDs in the dataset",
        "# TYPE app_loaded_event_ids_total gauge",
        f"app_loaded_event_ids_total {dataset_gauges['event_ids']}",
        "# HELP app_requests_total Total HTTP requests received by the application",
        "# TYPE app_requests_total counter",
    ]

    with request_lock:
        for (endpoint, method), value in sorted(request_metrics.items()):
            safe_endpoint = str(endpoint).replace('"', "")
            lines.append(
                f'app_requests_total{{endpoint="{safe_endpoint}",method="{method}"}} {value}'
            )

    return "\n".join(lines) + "\n"


def get_filter_options(df):
    def values_for(column, limit=None):
        if column not in df.columns:
            return []
        values = sorted(df[column].dropna().astype(str).unique().tolist())
        return values[:limit] if limit else values

    return {
        "providers": values_for("provider"),
        "levels": values_for("level"),
        "event_ids": values_for("event_id", limit=300),
    }


def apply_filters(df, args):
    filtered = df.copy()

    provider = args.get("provider", "").strip()
    level = args.get("level", "").strip()
    event_id = args.get("event_id", "").strip()
    search = args.get("search", "").strip()
    only_anomalies = args.get("only_anomalies") == "1"

    if provider and "provider" in filtered.columns:
        filtered = filtered[filtered["provider"].astype(str) == provider]

    if level and "level" in filtered.columns:
        filtered = filtered[filtered["level"].astype(str) == level]

    if event_id and "event_id" in filtered.columns:
        filtered = filtered[filtered["event_id"].astype(str) == event_id]

    if search and "message" in filtered.columns:
        filtered = filtered[
            filtered["message"].fillna("").str.contains(search, case=False, na=False)
        ]

    if only_anomalies and "ensemble_is_anomaly" in filtered.columns:
        filtered = filtered[filtered["ensemble_is_anomaly"] == 1]

    return filtered


def build_metrics(df):
    anomaly_count = 0
    if "ensemble_is_anomaly" in df.columns:
        anomaly_count = int(df["ensemble_is_anomaly"].fillna(0).sum())

    return {
        "total_rows": f"{len(df):,}",
        "providers": df["provider"].nunique(dropna=True) if "provider" in df.columns else 0,
        "event_ids": df["event_id"].nunique(dropna=True) if "event_id" in df.columns else 0,
        "anomalies": anomaly_count,
    }


def format_dataframe(df, limit):
    display_df = df.copy().head(limit)

    if "timestamp" in display_df.columns:
        display_df["timestamp"] = (
            pd.to_datetime(display_df["timestamp"], errors="coerce")
            .dt.strftime("%Y-%m-%d %H:%M:%S")
            .fillna("N/A")
        )

    display_df = display_df.fillna("")
    return display_df.to_dict(orient="records"), list(display_df.columns)


@app.before_request
def count_requests():
    update_request_counter()


@app.route("/metrics")
def metrics():
    df, _ = load_dataframe()
    update_dataset_gauges(df)
    return Response(build_metrics_payload(), mimetype="text/plain; version=0.0.4")


@app.route("/health")
def health():
    df, source = load_dataframe()
    update_dataset_gauges(df)
    return {
        "status": "ok" if df is not None else "missing_dataset",
        "dataset_source": source,
        "rows": 0 if df is None else len(df),
    }


@app.route("/")
def index():
    df, source = load_dataframe()
    update_dataset_gauges(df)
    if df is None:
        return render_template("index.html", error="No dataset found. Run python.py first.")

    filter_options = get_filter_options(df)
    filtered_df = apply_filters(df, request.args)
    metrics = build_metrics(filtered_df)

    table_rows, table_columns = format_dataframe(filtered_df, limit=250)

    suspicious_rows = []
    suspicious_columns = []
    if "ensemble_is_anomaly" in filtered_df.columns:
        suspicious_df = filtered_df[filtered_df["ensemble_is_anomaly"] == 1].sort_values(
            by=["anomaly_votes", "isolation_forest_score"],
            ascending=[False, False],
            na_position="last",
        )
        suspicious_rows, suspicious_columns = format_dataframe(suspicious_df, limit=50)

    return render_template(
        "index.html",
        error=None,
        source=source,
        metrics=metrics,
        filter_options=filter_options,
        filters={
            "provider": request.args.get("provider", ""),
            "level": request.args.get("level", ""),
            "event_id": request.args.get("event_id", ""),
            "search": request.args.get("search", ""),
            "only_anomalies": request.args.get("only_anomalies") == "1",
        },
        table_rows=table_rows,
        table_columns=table_columns,
        suspicious_rows=suspicious_rows,
        suspicious_columns=suspicious_columns,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
