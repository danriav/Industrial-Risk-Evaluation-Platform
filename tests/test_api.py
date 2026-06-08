from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from src.api.database import get_db
from src.api.main import app
from src.api.config import settings
from src.api.ml import load_model_bundle, predict_risk
from src.api.security import require_basic_auth


class BrokenSession:
    def execute(self, *args, **kwargs):
        raise OperationalError("select 1", {}, Exception("database unavailable"))


class BrokenModel:
    def predict(self, frame):
        raise RuntimeError("model failed")


def override_auth() -> str:
    return "backend_test"


def override_broken_db():
    yield BrokenSession()


class ApiTests(unittest.TestCase):
    def setUp(self) -> None:
        app.dependency_overrides.clear()
        self.client = TestClient(app, raise_server_exceptions=False)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_health_and_metrics(self) -> None:
        health = self.client.get("/health")
        metrics = self.client.get("/metrics")

        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.json(), {"status": "ok", "service": "mero-api"})
        self.assertEqual(metrics.status_code, 200)
        self.assertIn("# HELP", metrics.text)

    def test_protected_endpoint_requires_authentication(self) -> None:
        response = self.client.get("/api/v1/failure-catalog")

        self.assertEqual(response.status_code, 401)

    def test_database_errors_are_controlled(self) -> None:
        app.dependency_overrides[require_basic_auth] = override_auth
        app.dependency_overrides[get_db] = override_broken_db

        response = self.client.get("/api/v1/failure-catalog")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {"detail": "Database is unavailable"})
        self.assertNotIn("postgresql", response.text.lower())

    def test_prediction_contract_uses_model_result(self) -> None:
        app.dependency_overrides[require_basic_auth] = override_auth
        payload = {
            "equipment_id": "00000000-0000-0000-0000-000000000040",
            "observed_at": "2026-05-22T15:00:00Z",
            "features": {
                "equipment_class": "centrifugal_pump",
                "temperature_c": 82.4,
                "sensor_quality": "good",
            },
        }

        with patch("src.api.routers.predictions.predict_risk", return_value=("high", 0.87, "test_model")):
            response = self.client.post("/api/v1/predictions/risk", json=payload)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["risk_label"], "high")
        self.assertEqual(response.json()["risk_score"], 0.87)
        self.assertEqual(response.json()["model_version"], "test_model")

    def test_prediction_rejects_feature_contract_mismatch(self) -> None:
        bundle = {
            "model": object(),
            "numeric_columns": ["temperature_c"],
            "categorical_columns": ["equipment_class"],
        }

        with patch("src.api.ml.load_model_bundle", return_value=bundle):
            with self.assertRaises(HTTPException) as error:
                predict_risk({"temperature_c": 80.0, "unexpected": "value"})

        self.assertEqual(error.exception.status_code, 422)
        self.assertEqual(error.exception.detail["missing_features"], ["equipment_class"])
        self.assertEqual(error.exception.detail["extra_features"], ["unexpected"])

    def test_prediction_model_errors_are_clean(self) -> None:
        bundle = {
            "model": BrokenModel(),
            "numeric_columns": ["temperature_c"],
            "categorical_columns": ["equipment_class"],
        }

        with patch("src.api.ml.load_model_bundle", return_value=bundle):
            with self.assertRaises(HTTPException) as error:
                predict_risk({"temperature_c": 80.0, "equipment_class": "centrifugal_pump"})

        self.assertEqual(error.exception.status_code, 503)
        self.assertEqual(error.exception.detail, "Model prediction failed")

    def test_missing_model_artifact_returns_clean_error(self) -> None:
        app.dependency_overrides[require_basic_auth] = override_auth
        original_model_path = settings.model_path
        payload = {
            "equipment_id": "00000000-0000-0000-0000-000000000040",
            "observed_at": "2026-06-03T23:00:00Z",
            "features": {
                "equipment_class": "centrifugal_pump",
                "temperature_c": 68.0,
                "vibration_mm_s": 3.2,
                "pressure_bar": 8.2,
                "rpm": 1780,
                "operating_hours": 12043,
                "load_pct": 63.0,
                "sensor_quality": "good",
            },
        }

        try:
            load_model_bundle.cache_clear()
            object.__setattr__(settings, "model_path", Path("artifacts/models/missing_model.joblib"))
            response = self.client.post("/api/v1/predictions/risk", json=payload)
        finally:
            object.__setattr__(settings, "model_path", original_model_path)
            load_model_bundle.cache_clear()

        self.assertEqual(response.status_code, 503)
        self.assertIn("Model artifact not found", response.json()["detail"])
        self.assertNotIn("traceback", response.text.lower())


if __name__ == "__main__":
    unittest.main()
