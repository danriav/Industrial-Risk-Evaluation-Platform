from __future__ import annotations

import base64
import json
import os
import unittest
import urllib.request


def _request(path: str, method: str = "GET", body: dict[str, object] | None = None) -> tuple[int, str]:
    base_url = os.getenv("API_BASE_URL", "http://127.0.0.1:8080").rstrip("/")
    username = os.environ["BASIC_AUTH_USERNAME"]
    password = os.environ["BASIC_AUTH_PASSWORD"]
    token = base64.b64encode(f"{username}:{password}".encode("ascii")).decode("ascii")
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Basic {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, response.read().decode("utf-8")


@unittest.skipUnless(os.getenv("RUN_DEMO_INTEGRATION") == "1", "live demo integration disabled")
class DemoIntegrationTests(unittest.TestCase):
    def test_demo_endpoints_and_prediction(self) -> None:
        required_env = {"BASIC_AUTH_USERNAME", "BASIC_AUTH_PASSWORD"}
        missing_env = sorted(name for name in required_env if not os.getenv(name))
        if missing_env:
            self.skipTest("missing environment: " + ", ".join(missing_env))

        endpoints = [
            "/api/v1/assets/hierarchy",
            "/api/v1/failure-catalog",
            "/api/v1/sensor-observations",
            "/api/v1/maintenance-logs",
        ]
        for endpoint in endpoints:
            status_code, payload = _request(endpoint)
            self.assertEqual(status_code, 200)
            self.assertIn("items", json.loads(payload))

        prediction_payload = {
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
        status_code, payload = _request("/api/v1/predictions/risk", method="POST", body=prediction_payload)
        prediction = json.loads(payload)

        self.assertEqual(status_code, 200)
        self.assertIn(prediction["risk_label"], {"low", "medium", "high"})
        self.assertEqual(prediction["model_version"], "random_forest")
        self.assertEqual(prediction["feature_count"], 8)


if __name__ == "__main__":
    unittest.main()
