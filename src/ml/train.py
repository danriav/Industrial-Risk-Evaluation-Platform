from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import joblib
import pandas as pd
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import KNNImputer, SimpleImputer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler


DEFAULT_EXCLUDED_COLUMNS = {
    "observation_id",
    "equipment_id",
    "observed_at",
    "maintenance_log_id",
    "reported_at",
}


def load_training_frame(input_path: Path) -> pd.DataFrame:
    if input_path.suffix.lower() == ".parquet":
        return pd.read_parquet(input_path)
    return pd.read_csv(input_path)


def build_pipeline(
    numeric_columns: list[str],
    categorical_columns: list[str],
    random_state: int,
    smote_k_neighbors: int,
) -> Pipeline:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", KNNImputer(n_neighbors=5, weights="distance")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, numeric_columns),
            ("categorical", categorical_pipeline, categorical_columns),
        ]
    )

    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("smote", SMOTE(k_neighbors=smote_k_neighbors, random_state=random_state)),
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=300,
                    class_weight="balanced_subsample",
                    min_samples_leaf=2,
                    n_jobs=-1,
                    random_state=random_state,
                ),
            ),
        ]
    )


def split_features_target(
    frame: pd.DataFrame,
    target_column: str,
) -> tuple[pd.DataFrame, pd.Series, list[str], list[str]]:
    if target_column not in frame.columns:
        raise ValueError(f"Target column {target_column!r} was not found.")

    candidate_features = [
        column
        for column in frame.columns
        if column != target_column and column not in DEFAULT_EXCLUDED_COLUMNS
    ]
    X = frame[candidate_features]
    y = frame[target_column]

    numeric_columns = X.select_dtypes(include=["number", "bool"]).columns.tolist()
    categorical_columns = [column for column in candidate_features if column not in numeric_columns]

    if not numeric_columns and not categorical_columns:
        raise ValueError("No usable feature columns were found.")

    return X, y, numeric_columns, categorical_columns


def train_model(
    input_path: Path,
    output_path: Path,
    metrics_path: Path,
    target_column: str,
    random_state: int,
    test_size: float,
    split_strategy: str,
    time_column: str,
    model_version: str | None,
    versioned_output_dir: Path | None,
) -> None:
    frame = load_training_frame(input_path).drop_duplicates()
    frame = frame.dropna(subset=[target_column])
    X, y, numeric_columns, categorical_columns = split_features_target(frame, target_column)

    if split_strategy == "temporal":
        if time_column not in frame.columns:
            raise ValueError(f"Temporal split requires time column {time_column!r}.")
        ordered = frame.assign(_split_time=pd.to_datetime(frame[time_column], errors="coerce"))
        ordered = ordered.dropna(subset=["_split_time"]).sort_values("_split_time")
        if ordered.empty:
            raise ValueError(f"Temporal split found no valid timestamps in {time_column!r}.")
        X, y, numeric_columns, categorical_columns = split_features_target(
            ordered.drop(columns=["_split_time"]),
            target_column,
        )
        test_count = max(1, int(len(ordered) * test_size))
        if test_count >= len(ordered):
            raise ValueError("Temporal split leaves no training rows; reduce --test-size.")
        X_train, X_test = X.iloc[:-test_count], X.iloc[-test_count:]
        y_train, y_test = y.iloc[:-test_count], y.iloc[-test_count:]
    else:
        stratify = y if y.nunique(dropna=True) > 1 else None
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify,
        )

    class_counts = y_train.value_counts()
    if class_counts.size < 2:
        raise ValueError("Training data must contain at least two target classes.")
    if class_counts.min() < 2:
        raise ValueError("SMOTE requires at least two samples in every target class.")

    smote_k_neighbors = min(5, int(class_counts.min()) - 1)
    pipeline = build_pipeline(numeric_columns, categorical_columns, random_state, smote_k_neighbors)
    pipeline.fit(X_train, y_train)

    predictions = pipeline.predict(X_test)
    labels = sorted(y.dropna().astype(str).unique().tolist())
    report = classification_report(y_test, predictions, labels=labels, output_dict=True, zero_division=0)

    baseline = DummyClassifier(strategy="most_frequent")
    baseline.fit(X_train, y_train)
    baseline_predictions = baseline.predict(X_test)
    baseline_report = classification_report(
        y_test,
        baseline_predictions,
        labels=labels,
        output_dict=True,
        zero_division=0,
    )

    bundle = {
        "model": pipeline,
        "target_column": target_column,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "model_version": model_version,
        "split_strategy": split_strategy,
    }
    metrics = {
        "model_version": model_version,
        "trained_at": datetime.now(UTC).isoformat(),
        "input_path": str(input_path),
        "target_column": target_column,
        "split_strategy": split_strategy,
        "time_column": time_column if split_strategy == "temporal" else None,
        "class_distribution": y.value_counts().to_dict(),
        "model": report,
        "baseline_most_frequent": baseline_report,
        "confusion_matrix": {
            "labels": labels,
            "matrix": confusion_matrix(y_test, predictions, labels=labels).tolist(),
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, output_path)
    if model_version and versioned_output_dir is not None:
        versioned_output_dir.mkdir(parents=True, exist_ok=True)
        versioned_path = versioned_output_dir / f"random_forest_{model_version}.joblib"
        joblib.dump(bundle, versioned_path)
        metrics["versioned_model_path"] = str(versioned_path)
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train the offline MERO risk model.")
    parser.add_argument("--input", required=True, type=Path, help="CSV or Parquet training dataset.")
    parser.add_argument("--target", default="failure_label", help="Target class column.")
    parser.add_argument("--output", default=Path("artifacts/models/random_forest.joblib"), type=Path)
    parser.add_argument("--metrics", default=Path("artifacts/models/random_forest_metrics.json"), type=Path)
    parser.add_argument("--random-state", default=42, type=int)
    parser.add_argument("--test-size", default=0.2, type=float)
    parser.add_argument("--split-strategy", choices=["random", "temporal"], default="random")
    parser.add_argument("--time-column", default="observed_at")
    parser.add_argument("--model-version", default=None)
    parser.add_argument("--versioned-output-dir", default=Path("artifacts/models"), type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    train_model(
        input_path=args.input,
        output_path=args.output,
        metrics_path=args.metrics,
        target_column=args.target,
        random_state=args.random_state,
        test_size=args.test_size,
        split_strategy=args.split_strategy,
        time_column=args.time_column,
        model_version=args.model_version,
        versioned_output_dir=args.versioned_output_dir,
    )
