from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from scipy import sparse
from sklearn.cluster import MiniBatchKMeans
from sklearn.compose import ColumnTransformer
from sklearn.decomposition import TruncatedSVD
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDOneClassSVM


DATASET_PATH = Path("logs_dataset.csv")
MODEL_DIR = Path("trained_models")
REPORT_PATH = MODEL_DIR / "model_training_report.txt"
SCORES_PATH = MODEL_DIR / "anomaly_scores.csv"


def add_time_features(df):
    """Create lightweight time-based fields from the timestamp column."""
    enriched = df.copy()
    timestamps = pd.to_datetime(enriched["timestamp"], errors="coerce")
    enriched["hour"] = timestamps.dt.hour.fillna(-1).astype(int).astype(str)
    enriched["day_of_week"] = timestamps.dt.dayofweek.fillna(-1).astype(int).astype(str)
    enriched["message"] = enriched["message"].fillna("")
    return enriched


def squeeze_text_column(values):
    """Turn a single-column dataframe into a 1D array for TF-IDF."""
    return values.squeeze()


def build_preprocessor():
    categorical_columns = ["event_id", "level", "provider", "computer", "hour", "day_of_week"]
    text_column = "message"

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    text_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="constant", fill_value="")),
            ("flatten", FunctionTransformer(squeeze_text_column, validate=False)),
            ("tfidf", TfidfVectorizer(max_features=300, ngram_range=(1, 2))),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, categorical_columns),
            ("text", text_pipeline, [text_column]),
        ]
    )


def build_feature_matrix(df):
    pipeline = Pipeline(
        steps=[
            ("time_features", FunctionTransformer(add_time_features, validate=False)),
            ("preprocessor", build_preprocessor()),
            ("svd", TruncatedSVD(n_components=30, random_state=42)),
        ]
    )
    features = pipeline.fit_transform(df)
    return pipeline, features


def train_models(features):
    models = {
        "isolation_forest": IsolationForest(
            n_estimators=200,
            contamination=0.05,
            random_state=42,
            n_jobs=1,
        ),
        "local_outlier_factor": LocalOutlierFactor(
            contamination=0.05,
            n_neighbors=35,
            novelty=True,
        ),
        "sgd_one_class_svm": SGDOneClassSVM(
            nu=0.05,
            random_state=42,
        ),
    }

    results = {}

    for name, model in models.items():
        model.fit(features)
        scores = -model.score_samples(features)
        threshold = np.quantile(scores, 0.95)
        predictions = (scores >= threshold).astype(int)
        results[name] = {
            "model": model,
            "scores": scores,
            "predictions": predictions,
            "anomaly_count": int(predictions.sum()),
            "threshold": float(threshold),
        }

    kmeans = MiniBatchKMeans(n_clusters=8, random_state=42, batch_size=1024, n_init=10)
    kmeans.fit(features)
    distances = kmeans.transform(features).min(axis=1)
    threshold = np.quantile(distances, 0.95)
    predictions = (distances >= threshold).astype(int)
    results["mini_batch_kmeans"] = {
        "model": kmeans,
        "scores": distances,
        "predictions": predictions,
        "anomaly_count": int(predictions.sum()),
        "threshold": float(threshold),
    }

    return results


def save_results(df, feature_pipeline, results):
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(feature_pipeline, MODEL_DIR / "feature_pipeline.joblib")

    scores_df = df.copy()
    report_lines = [
        "AI Log Analyzer Model Training Report",
        "=" * 36,
        f"Rows used for training: {len(df)}",
        "",
        "Trained models:",
    ]

    for model_name, payload in results.items():
        joblib.dump(payload["model"], MODEL_DIR / f"{model_name}.joblib")
        scores_df[f"{model_name}_score"] = payload["scores"]
        scores_df[f"{model_name}_is_anomaly"] = payload["predictions"]

        report_lines.append(
            f"- {model_name}: anomalies={payload['anomaly_count']}, threshold={payload['threshold']:.4f}"
        )

    anomaly_vote_columns = [f"{name}_is_anomaly" for name in results]
    scores_df["anomaly_votes"] = scores_df[anomaly_vote_columns].sum(axis=1)
    scores_df["ensemble_is_anomaly"] = (scores_df["anomaly_votes"] >= 2).astype(int)

    top_columns = [
        "timestamp",
        "provider",
        "event_id",
        "level",
        "message",
        "anomaly_votes",
        "ensemble_is_anomaly",
    ]
    top_anomalies = scores_df.sort_values(
        by=["anomaly_votes", "isolation_forest_score"],
        ascending=[False, False],
    ).head(10)

    report_lines.append("")
    report_lines.append(
        f"Ensemble anomalies (flagged by at least 2 models): {int(scores_df['ensemble_is_anomaly'].sum())}"
    )
    report_lines.append("")
    report_lines.append("Top 10 suspicious log rows:")

    for row in top_anomalies[top_columns].fillna("N/A").itertuples(index=False):
        report_lines.append(
            f"- time={row.timestamp}, provider={row.provider}, event_id={row.event_id}, "
            f"level={row.level}, votes={row.anomaly_votes}, message={str(row.message)[:140]}"
        )

    scores_df.to_csv(SCORES_PATH, index=False)
    REPORT_PATH.write_text("\n".join(report_lines), encoding="utf-8")


def main():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            f"Dataset not found: {DATASET_PATH}. Run python.py first to generate logs_dataset.csv."
        )

    df = pd.read_csv(DATASET_PATH)
    feature_pipeline, features = build_feature_matrix(df)

    if sparse.issparse(features):
        features = features.toarray()

    results = train_models(features)
    save_results(df, feature_pipeline, results)

    print(f"Models saved in {MODEL_DIR}")
    print(f"Training report saved to {REPORT_PATH}")
    print(f"Scored dataset saved to {SCORES_PATH}")


if __name__ == "__main__":
    main()
