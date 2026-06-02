from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status

from .config import settings


RISK_LABEL_MAP = {
    "normal": "low",
    "warning": "medium",
    "critical": "high",
    "low": "low",
    "medium": "medium",
    "high": "high",
}
SUPPORTED_RISK_LABELS = {"low", "medium", "high"}


@lru_cache(maxsize=1)
def load_model_bundle() -> dict[str, Any]:
    model_path = settings.model_path
    if not model_path.exists():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model artifact not found at {model_path}",
        )

    try:
        import joblib
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model runtime dependency joblib is not installed",
        ) from exc

    bundle = joblib.load(model_path)
    required_keys = {"model", "numeric_columns", "categorical_columns"}
    if not isinstance(bundle, dict) or not required_keys.issubset(bundle):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model artifact has an unsupported format",
        )
    return bundle


def predict_risk(features: dict[str, Any]) -> tuple[str, float, str]:
    bundle = load_model_bundle()
    model = bundle["model"]
    feature_columns = list(bundle.get("numeric_columns", [])) + list(bundle.get("categorical_columns", []))
    if not feature_columns:
        feature_columns = sorted(features.keys())

    missing_features = [column for column in feature_columns if column not in features]
    extra_features = sorted(column for column in features if column not in feature_columns)
    if missing_features or extra_features:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Prediction features do not match the trained model contract",
                "required_features": feature_columns,
                "missing_features": missing_features,
                "extra_features": extra_features,
            },
        )

    try:
        import pandas as pd
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model runtime dependency pandas is not installed",
        ) from exc

    frame = pd.DataFrame([{column: features.get(column) for column in feature_columns}])
    try:
        prediction = model.predict(frame)[0]
        risk_label = RISK_LABEL_MAP.get(str(prediction))
        if risk_label not in SUPPORTED_RISK_LABELS:
            raise ValueError("unsupported model label")

        risk_score = 1.0
        if hasattr(model, "predict_proba"):
            probabilities = model.predict_proba(frame)[0]
            risk_score = float(max(probabilities))
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Model input could not be processed",
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model prediction failed",
        ) from exc

    model_version = Path(settings.model_path).stem
    return risk_label, risk_score, model_version
