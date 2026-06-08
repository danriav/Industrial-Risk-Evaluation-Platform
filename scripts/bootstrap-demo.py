from __future__ import annotations

import argparse
import base64
import importlib.util
import os
import re
import subprocess
import sys
import time
from http.client import RemoteDisconnected
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ENV_PATH = ROOT / ".env"
DATASET_PATH = ROOT / "data" / "training_seed.csv"
MODEL_PATH = ROOT / "artifacts" / "models" / "random_forest.joblib"
METRICS_PATH = ROOT / "artifacts" / "models" / "random_forest_metrics.json"
MIGRATIONS = [ROOT / "src" / "db" / "migrations" / "001_iso14224_assets.sql"]


DEMO_TENANT_ID = "00000000-0000-0000-0000-000000000001"
DEMO_BASE_TIME = "2026-06-03T10:00:00Z"

DEMO_PLANTS = [
    {
        "plant_id": "00000000-0000-0000-0000-000000000010",
        "tenant_id": DEMO_TENANT_ID,
        "plant_code": "PLT-01",
        "plant_name": "Planta Demo Norte",
        "last_known_state": "operational",
    },
    {
        "plant_id": "00000000-0000-0000-0000-000000000011",
        "tenant_id": DEMO_TENANT_ID,
        "plant_code": "PLT-02",
        "plant_name": "Planta Demo Sur",
        "last_known_state": "requires_review",
    },
]

DEMO_LINES = [
    {
        "line_id": "00000000-0000-0000-0000-000000000020",
        "plant_id": "00000000-0000-0000-0000-000000000010",
        "line_code": "LN-01",
        "line_name": "Linea de Bombeo",
        "last_known_state": "operational",
    },
    {
        "line_id": "00000000-0000-0000-0000-000000000021",
        "plant_id": "00000000-0000-0000-0000-000000000010",
        "line_code": "LN-02",
        "line_name": "Linea de Transporte",
        "last_known_state": "operational",
    },
    {
        "line_id": "00000000-0000-0000-0000-000000000022",
        "plant_id": "00000000-0000-0000-0000-000000000011",
        "line_code": "LN-03",
        "line_name": "Linea de Mezclado",
        "last_known_state": "requires_review",
    },
]

DEMO_CELLS = [
    {
        "cell_id": "00000000-0000-0000-0000-000000000030",
        "line_id": "00000000-0000-0000-0000-000000000020",
        "cell_code": "CELL-01",
        "cell_name": "Celula de Bombeo Primaria",
        "last_known_state": "operational",
    },
    {
        "cell_id": "00000000-0000-0000-0000-000000000031",
        "line_id": "00000000-0000-0000-0000-000000000020",
        "cell_code": "CELL-02",
        "cell_name": "Celula de Compresion",
        "last_known_state": "requires_review",
    },
    {
        "cell_id": "00000000-0000-0000-0000-000000000032",
        "line_id": "00000000-0000-0000-0000-000000000021",
        "cell_code": "CELL-03",
        "cell_name": "Celula de Transportadores",
        "last_known_state": "operational",
    },
    {
        "cell_id": "00000000-0000-0000-0000-000000000033",
        "line_id": "00000000-0000-0000-0000-000000000022",
        "cell_code": "CELL-04",
        "cell_name": "Celula de Mezclado",
        "last_known_state": "requires_review",
    },
]

DEMO_EQUIPMENT = [
    {
        "equipment_id": "00000000-0000-0000-0000-000000000040",
        "cell_id": "00000000-0000-0000-0000-000000000030",
        "equipment_code": "PUMP-01",
        "equipment_name": "Bomba centrifuga principal",
        "equipment_class": "centrifugal_pump",
        "manufacturer": "Demo Pumps",
        "model": "CP-1800",
        "serial_number": "DEMO-PUMP-01",
        "installed_at": "2024-01-15",
        "last_known_state": "requires_review",
    },
    {
        "equipment_id": "00000000-0000-0000-0000-000000000041",
        "cell_id": "00000000-0000-0000-0000-000000000030",
        "equipment_code": "PUMP-02",
        "equipment_name": "Bomba centrifuga auxiliar",
        "equipment_class": "centrifugal_pump",
        "manufacturer": "Demo Pumps",
        "model": "CP-1500",
        "serial_number": "DEMO-PUMP-02",
        "installed_at": "2024-02-10",
        "last_known_state": "operational",
    },
    {
        "equipment_id": "00000000-0000-0000-0000-000000000042",
        "cell_id": "00000000-0000-0000-0000-000000000031",
        "equipment_code": "COMP-01",
        "equipment_name": "Compresor de aire principal",
        "equipment_class": "compressor",
        "manufacturer": "Demo Air",
        "model": "AC-3600",
        "serial_number": "DEMO-COMP-01",
        "installed_at": "2023-11-01",
        "last_known_state": "requires_review",
    },
    {
        "equipment_id": "00000000-0000-0000-0000-000000000043",
        "cell_id": "00000000-0000-0000-0000-000000000031",
        "equipment_code": "COMP-02",
        "equipment_name": "Compresor de respaldo",
        "equipment_class": "compressor",
        "manufacturer": "Demo Air",
        "model": "AC-3200",
        "serial_number": "DEMO-COMP-02",
        "installed_at": "2023-12-05",
        "last_known_state": "operational",
    },
    {
        "equipment_id": "00000000-0000-0000-0000-000000000044",
        "cell_id": "00000000-0000-0000-0000-000000000032",
        "equipment_code": "CONV-01",
        "equipment_name": "Transportador de alimentacion",
        "equipment_class": "conveyor",
        "manufacturer": "Demo Motion",
        "model": "CV-900",
        "serial_number": "DEMO-CONV-01",
        "installed_at": "2022-09-20",
        "last_known_state": "operational",
    },
    {
        "equipment_id": "00000000-0000-0000-0000-000000000045",
        "cell_id": "00000000-0000-0000-0000-000000000032",
        "equipment_code": "CONV-02",
        "equipment_name": "Transportador de descarga",
        "equipment_class": "conveyor",
        "manufacturer": "Demo Motion",
        "model": "CV-850",
        "serial_number": "DEMO-CONV-02",
        "installed_at": "2022-09-21",
        "last_known_state": "unknown",
    },
    {
        "equipment_id": "00000000-0000-0000-0000-000000000046",
        "cell_id": "00000000-0000-0000-0000-000000000033",
        "equipment_code": "MIX-01",
        "equipment_name": "Mezclador intensivo",
        "equipment_class": "mixer",
        "manufacturer": "Demo Mix",
        "model": "MX-1250",
        "serial_number": "DEMO-MIX-01",
        "installed_at": "2023-05-14",
        "last_known_state": "requires_review",
    },
    {
        "equipment_id": "00000000-0000-0000-0000-000000000047",
        "cell_id": "00000000-0000-0000-0000-000000000033",
        "equipment_code": "MIX-02",
        "equipment_name": "Mezclador secundario",
        "equipment_class": "mixer",
        "manufacturer": "Demo Mix",
        "model": "MX-1000",
        "serial_number": "DEMO-MIX-02",
        "installed_at": "2023-06-03",
        "last_known_state": "unknown",
    },
]

DEMO_FAILURE_CATALOG = [
    ("BRG_OVERHEAT", "mechanical", "bearing_overheating", "ISO14224", True),
    ("SEAL_LEAK", "process", "seal_leakage", "ISO14224", True),
    ("MISALIGNMENT", "mechanical", "shaft_misalignment", "ISO14224", True),
    ("HIGH_VIBRATION", "mechanical", "excessive_vibration", "ISO14224", True),
    ("MOTOR_OVERLOAD", "electrical", "motor_overload", "ISO14224", True),
    ("SENSOR_FAULT", "instrumentation", "sensor_signal_fault", "ISO14224", True),
]

DEMO_SENSOR_OBSERVATIONS = [
    {
        "observation_id": "00000000-0000-0000-0000-000000000050",
        "equipment_id": "00000000-0000-0000-0000-000000000040",
        "observed_at": "2026-06-03T09:50:00Z",
        "temperature_c": 82.4,
        "vibration_mm_s": 4.7,
        "pressure_bar": 9.1,
        "rpm": 1780.0,
        "operating_hours": 1280.0,
        "load_pct": 76.5,
        "sensor_quality": "good",
    },
    {
        "observation_id": "00000000-0000-0000-0000-000000000051",
        "equipment_id": "00000000-0000-0000-0000-000000000041",
        "observed_at": "2026-06-03T09:51:00Z",
        "temperature_c": 64.8,
        "vibration_mm_s": 2.6,
        "pressure_bar": 7.8,
        "rpm": 1765.0,
        "operating_hours": 920.0,
        "load_pct": 58.0,
        "sensor_quality": "good",
    },
    {
        "observation_id": "00000000-0000-0000-0000-000000000052",
        "equipment_id": "00000000-0000-0000-0000-000000000042",
        "observed_at": "2026-06-03T09:52:00Z",
        "temperature_c": 94.2,
        "vibration_mm_s": 8.9,
        "pressure_bar": 14.8,
        "rpm": 3630.0,
        "operating_hours": 4420.0,
        "load_pct": 96.0,
        "sensor_quality": "degraded",
    },
    {
        "observation_id": "00000000-0000-0000-0000-000000000053",
        "equipment_id": "00000000-0000-0000-0000-000000000043",
        "observed_at": "2026-06-03T09:53:00Z",
        "temperature_c": 71.5,
        "vibration_mm_s": 3.8,
        "pressure_bar": 10.1,
        "rpm": 3580.0,
        "operating_hours": 2760.0,
        "load_pct": 68.0,
        "sensor_quality": "good",
    },
    {
        "observation_id": "00000000-0000-0000-0000-000000000054",
        "equipment_id": "00000000-0000-0000-0000-000000000044",
        "observed_at": "2026-06-03T09:54:00Z",
        "temperature_c": 59.1,
        "vibration_mm_s": 2.1,
        "pressure_bar": 3.2,
        "rpm": 890.0,
        "operating_hours": 6020.0,
        "load_pct": 54.0,
        "sensor_quality": "good",
    },
    {
        "observation_id": "00000000-0000-0000-0000-000000000056",
        "equipment_id": "00000000-0000-0000-0000-000000000046",
        "observed_at": "2026-06-03T09:56:00Z",
        "temperature_c": 78.8,
        "vibration_mm_s": 5.9,
        "pressure_bar": 6.4,
        "rpm": 1260.0,
        "operating_hours": 3180.0,
        "load_pct": 88.0,
        "sensor_quality": "degraded",
    },
]

DEMO_MAINTENANCE_LOGS = [
    {
        "maintenance_log_id": "00000000-0000-0000-0000-000000000060",
        "equipment_id": "00000000-0000-0000-0000-000000000040",
        "reported_at": "2026-06-03T10:05:00Z",
        "operator_state": "requires_review",
        "failure_code": "BRG_OVERHEAT",
        "free_text_observation": "Demo sintetico: operador reporta temperatura elevada en rodamiento.",
    },
    {
        "maintenance_log_id": "00000000-0000-0000-0000-000000000061",
        "equipment_id": "00000000-0000-0000-0000-000000000042",
        "reported_at": "2026-06-03T10:10:00Z",
        "operator_state": "down",
        "failure_code": "HIGH_VIBRATION",
        "free_text_observation": "Demo sintetico: compresor detenido para inspeccion por vibracion alta.",
    },
    {
        "maintenance_log_id": "00000000-0000-0000-0000-000000000062",
        "equipment_id": "00000000-0000-0000-0000-000000000046",
        "reported_at": "2026-06-03T10:15:00Z",
        "operator_state": "requires_review",
        "failure_code": "MOTOR_OVERLOAD",
        "free_text_observation": "Demo sintetico: carga elevada y sensor degradado, revisar motor.",
    },
]

DEMO_THRESHOLDS = [
    {
        "threshold_id": "00000000-0000-0000-0000-000000000070",
        "equipment_class": "centrifugal_pump",
        "variable_name": "temperature_c",
        "min_value": 0,
        "max_value": 85,
        "max_delta_per_hour": 12,
        "severity": "high",
        "rationale": "Demo synthetic threshold for pump temperature review.",
    },
    {
        "threshold_id": "00000000-0000-0000-0000-000000000071",
        "equipment_class": "centrifugal_pump",
        "variable_name": "vibration_mm_s",
        "min_value": 0,
        "max_value": 7,
        "max_delta_per_hour": 2,
        "severity": "critical",
        "rationale": "Demo synthetic threshold for pump vibration review.",
    },
    {
        "threshold_id": "00000000-0000-0000-0000-000000000072",
        "equipment_class": "compressor",
        "variable_name": "temperature_c",
        "min_value": 0,
        "max_value": 92,
        "max_delta_per_hour": 10,
        "severity": "high",
        "rationale": "Demo synthetic threshold for compressor temperature review.",
    },
    {
        "threshold_id": "00000000-0000-0000-0000-000000000073",
        "equipment_class": "compressor",
        "variable_name": "vibration_mm_s",
        "min_value": 0,
        "max_value": 8.5,
        "max_delta_per_hour": 1.8,
        "severity": "critical",
        "rationale": "Demo synthetic threshold for compressor vibration review.",
    },
]


def load_dotenv(path: Path = ENV_PATH) -> None:
    if not path.exists():
        raise SystemExit(".env not found. Run: cp .env.example .env")

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def ensure_dependencies(auto_install: bool) -> None:
    required = {
        "joblib": "joblib",
        "pandas": "pandas",
        "sklearn": "scikit-learn",
        "imblearn": "imbalanced-learn",
        "sqlalchemy": "SQLAlchemy",
        "psycopg": "psycopg[binary]",
    }
    missing = [package for module, package in required.items() if importlib.util.find_spec(module) is None]
    if not missing:
        return
    if not auto_install:
        raise SystemExit(
            "Missing Python packages: "
            + ", ".join(missing)
            + ". Run: python -m pip install -r src/api/requirements.txt -r src/ml/requirements.txt"
        )

    print("Installing missing Python dependencies for demo bootstrap...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-r",
            str(ROOT / "src" / "api" / "requirements.txt"),
            "-r",
            str(ROOT / "src" / "ml" / "requirements.txt"),
        ],
        check=True,
        cwd=ROOT,
    )


def generate_training_seed(rows: int, random_state: int) -> None:
    from src.ml.prepare_seed_dataset import write_dataset

    write_dataset(DATASET_PATH, row_count=rows, random_state=random_state)
    print(f"Generated dataset: {DATASET_PATH.relative_to(ROOT)}")


def train_demo_model(random_state: int) -> None:
    from src.ml.train import train_model

    train_model(
        input_path=DATASET_PATH,
        output_path=MODEL_PATH,
        metrics_path=METRICS_PATH,
        target_column="failure_label",
        random_state=random_state,
        test_size=0.2,
        split_strategy="random",
        time_column="observed_at",
        model_version="demo_seed",
        versioned_output_dir=MODEL_PATH.parent,
    )
    print(f"Trained model: {MODEL_PATH.relative_to(ROOT)}")
    print(f"Wrote metrics: {METRICS_PATH.relative_to(ROOT)}")


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise SystemExit("DATABASE_URL is required in .env")
    return value


def sync_database_password_with_container() -> None:
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB")
    if not user or not password or not database:
        return
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", user) is None:
        print("Warning: skipping database password sync because POSTGRES_USER is not a simple identifier.")
        return

    escaped_password = password.replace("'", "''")
    statement = f"ALTER USER {user} WITH PASSWORD '{escaped_password}';"
    try:
        subprocess.run(
            ["docker", "compose", "exec", "-T", "database", "psql", "-U", user, "-d", database, "-c", statement],
            check=True,
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
        )
        print("Synchronized PostgreSQL user password with .env.")
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Warning: database password sync skipped or failed: {exc}")


def ensure_database_auth() -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url(), pool_pre_ping=True, future=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception:
        sync_database_password_with_container()


def apply_migrations() -> None:
    from sqlalchemy import create_engine

    engine = create_engine(database_url(), pool_pre_ping=True, future=True)
    with engine.begin() as connection:
        for migration_path in MIGRATIONS:
            connection.exec_driver_sql(migration_path.read_text(encoding="utf-8"))
            print(f"Applied migration: {migration_path.relative_to(ROOT)}")


def insert_demo_data() -> None:
    from sqlalchemy import create_engine, text

    engine = create_engine(database_url(), pool_pre_ping=True, future=True)
    demo_equipment_ids = [item["equipment_id"] for item in DEMO_EQUIPMENT]
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO tenants (tenant_id, legal_name)
                VALUES (:tenant_id, 'MERO Demo Synthetic Plant')
                ON CONFLICT (tenant_id) DO UPDATE SET
                    legal_name = EXCLUDED.legal_name,
                    updated_at = now()
                """
            ),
            {"tenant_id": DEMO_TENANT_ID},
        )

        for plant in DEMO_PLANTS:
            connection.execute(
                text(
                    """
                    INSERT INTO plants (
                        plant_id, tenant_id, plant_code, plant_name,
                        last_known_state, last_state_updated_at
                    )
                    VALUES (
                        :plant_id, :tenant_id, :plant_code, :plant_name,
                        :last_known_state, :last_state_updated_at
                    )
                    ON CONFLICT (plant_id) DO UPDATE SET
                        plant_code = EXCLUDED.plant_code,
                        plant_name = EXCLUDED.plant_name,
                        last_known_state = EXCLUDED.last_known_state,
                        last_state_updated_at = EXCLUDED.last_state_updated_at,
                        updated_at = now()
                    """
                ),
                {**plant, "last_state_updated_at": DEMO_BASE_TIME},
            )

        for line in DEMO_LINES:
            connection.execute(
                text(
                    """
                    INSERT INTO production_lines (
                        line_id, plant_id, line_code, line_name,
                        last_known_state, last_state_updated_at
                    )
                    VALUES (
                        :line_id, :plant_id, :line_code, :line_name,
                        :last_known_state, :last_state_updated_at
                    )
                    ON CONFLICT (line_id) DO UPDATE SET
                        plant_id = EXCLUDED.plant_id,
                        line_code = EXCLUDED.line_code,
                        line_name = EXCLUDED.line_name,
                        last_known_state = EXCLUDED.last_known_state,
                        last_state_updated_at = EXCLUDED.last_state_updated_at,
                        updated_at = now()
                    """
                ),
                {**line, "last_state_updated_at": DEMO_BASE_TIME},
            )

        for cell in DEMO_CELLS:
            connection.execute(
                text(
                    """
                    INSERT INTO cells (
                        cell_id, line_id, cell_code, cell_name,
                        last_known_state, last_state_updated_at
                    )
                    VALUES (
                        :cell_id, :line_id, :cell_code, :cell_name,
                        :last_known_state, :last_state_updated_at
                    )
                    ON CONFLICT (cell_id) DO UPDATE SET
                        line_id = EXCLUDED.line_id,
                        cell_code = EXCLUDED.cell_code,
                        cell_name = EXCLUDED.cell_name,
                        last_known_state = EXCLUDED.last_known_state,
                        last_state_updated_at = EXCLUDED.last_state_updated_at,
                        updated_at = now()
                    """
                ),
                {**cell, "last_state_updated_at": DEMO_BASE_TIME},
            )

        for equipment in DEMO_EQUIPMENT:
            connection.execute(
                text(
                    """
                    INSERT INTO equipment (
                        equipment_id, cell_id, equipment_code, equipment_name, equipment_class,
                        manufacturer, model, serial_number, installed_at,
                        last_known_state, last_state_updated_at
                    )
                    VALUES (
                        :equipment_id, :cell_id, :equipment_code, :equipment_name, :equipment_class,
                        :manufacturer, :model, :serial_number, :installed_at,
                        :last_known_state, :last_state_updated_at
                    )
                    ON CONFLICT (equipment_id) DO UPDATE SET
                        cell_id = EXCLUDED.cell_id,
                        equipment_code = EXCLUDED.equipment_code,
                        equipment_name = EXCLUDED.equipment_name,
                        equipment_class = EXCLUDED.equipment_class,
                        manufacturer = EXCLUDED.manufacturer,
                        model = EXCLUDED.model,
                        serial_number = EXCLUDED.serial_number,
                        installed_at = EXCLUDED.installed_at,
                        last_known_state = EXCLUDED.last_known_state,
                        last_state_updated_at = EXCLUDED.last_state_updated_at,
                        updated_at = now()
                    """
                ),
                {**equipment, "last_state_updated_at": DEMO_BASE_TIME},
            )

        for failure_code, failure_category, failure_mode, iso14224_reference, is_active in DEMO_FAILURE_CATALOG:
            connection.execute(
                text(
                    """
                    INSERT INTO failure_catalog (
                        failure_code, failure_category, failure_mode, iso14224_reference, is_active
                    )
                    VALUES (
                        :failure_code, :failure_category, :failure_mode, :iso14224_reference, :is_active
                    )
                    ON CONFLICT (failure_code) DO UPDATE SET
                        failure_category = EXCLUDED.failure_category,
                        failure_mode = EXCLUDED.failure_mode,
                        iso14224_reference = EXCLUDED.iso14224_reference,
                        is_active = EXCLUDED.is_active
                    """
                ),
                {
                    "failure_code": failure_code,
                    "failure_category": failure_category,
                    "failure_mode": failure_mode,
                    "iso14224_reference": iso14224_reference,
                    "is_active": is_active,
                },
            )

        for equipment_id in demo_equipment_ids:
            connection.execute(
                text("DELETE FROM sensor_observations WHERE equipment_id = :equipment_id"),
                {"equipment_id": equipment_id},
            )
        for observation in DEMO_SENSOR_OBSERVATIONS:
            connection.execute(
                text(
                    """
                    INSERT INTO sensor_observations (
                        observation_id, equipment_id, observed_at, temperature_c,
                        vibration_mm_s, pressure_bar, rpm, operating_hours,
                        load_pct, sensor_quality
                    )
                    VALUES (
                        :observation_id, :equipment_id, :observed_at, :temperature_c,
                        :vibration_mm_s, :pressure_bar, :rpm, :operating_hours,
                        :load_pct, :sensor_quality
                    )
                    """
                ),
                observation,
            )

        for maintenance_log in DEMO_MAINTENANCE_LOGS:
            connection.execute(
                text(
                    """
                    INSERT INTO maintenance_logs (
                        maintenance_log_id, equipment_id, reported_at, operator_state,
                        failure_code, free_text_observation
                    )
                    VALUES (
                        :maintenance_log_id, :equipment_id, :reported_at, :operator_state,
                        :failure_code, :free_text_observation
                    )
                    ON CONFLICT (maintenance_log_id) DO UPDATE SET
                        equipment_id = EXCLUDED.equipment_id,
                        reported_at = EXCLUDED.reported_at,
                        operator_state = EXCLUDED.operator_state,
                        failure_code = EXCLUDED.failure_code,
                        free_text_observation = EXCLUDED.free_text_observation
                    """
                ),
                maintenance_log,
            )

        for threshold in DEMO_THRESHOLDS:
            connection.execute(
                text(
                    """
                    INSERT INTO discrepancy_thresholds (
                        threshold_id, equipment_class, variable_name, min_value, max_value,
                        max_delta_per_hour, severity, rationale, approved_by, approved_at
                    )
                    VALUES (
                        :threshold_id, :equipment_class, :variable_name, :min_value, :max_value,
                        :max_delta_per_hour, :severity, :rationale, 'demo_bootstrap', :approved_at
                    )
                    ON CONFLICT (equipment_class, variable_name) DO UPDATE SET
                        min_value = EXCLUDED.min_value,
                        max_value = EXCLUDED.max_value,
                        max_delta_per_hour = EXCLUDED.max_delta_per_hour,
                        severity = EXCLUDED.severity,
                        rationale = EXCLUDED.rationale,
                        approved_by = EXCLUDED.approved_by,
                        approved_at = EXCLUDED.approved_at
                    """
                ),
                {**threshold, "approved_at": DEMO_BASE_TIME},
            )
    print(
        "Inserted synthetic demo hierarchy: "
        f"{len(DEMO_PLANTS)} plants, {len(DEMO_LINES)} lines, {len(DEMO_CELLS)} cells, "
        f"{len(DEMO_EQUIPMENT)} equipment, {len(DEMO_SENSOR_OBSERVATIONS)} sensor streams."
    )


def restart_backend(restart: bool) -> None:
    if not restart:
        return
    try:
        subprocess.run(["docker", "compose", "restart", "backend"], check=True, cwd=ROOT)
        print("Restarted backend container.")
    except (OSError, subprocess.CalledProcessError) as exc:
        print(f"Warning: backend restart skipped or failed: {exc}")


def api_check(skip: bool) -> None:
    if skip:
        return

    base_url = os.getenv("API_BASE_URL", "http://localhost:8080").rstrip("/")
    username = os.getenv("BASIC_AUTH_USERNAME", "")
    password = os.getenv("BASIC_AUTH_PASSWORD", "")
    if not username or not password:
        print("Warning: skipping API check because Basic Auth credentials are missing.")
        return

    credentials = base64.b64encode(f"{username}:{password}".encode("ascii")).decode("ascii")
    payload = (
        '{"equipment_id":"00000000-0000-0000-0000-000000000040",'
        '"observed_at":"2026-06-03T09:50:00Z",'
        '"features":{"equipment_class":"centrifugal_pump","temperature_c":82.4,'
        '"vibration_mm_s":4.7,"pressure_bar":9.1,"rpm":1780,'
        '"operating_hours":1280.0,"load_pct":76.5,"sensor_quality":"good"}}'
    ).encode("utf-8")

    for attempt in range(1, 7):
        try:
            request = Request(
                f"{base_url}/api/v1/predictions/risk",
                data=payload,
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                method="POST",
            )
            with urlopen(request, timeout=10) as response:
                body = response.read().decode("utf-8")
            print(f"Prediction API check passed: {body}")
            return
        except (HTTPError, RemoteDisconnected, TimeoutError, URLError) as exc:
            if attempt == 6:
                print(f"Warning: prediction API check failed after retries: {exc}")
                return
            time.sleep(2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bootstrap MERO demo data, model, migrations, and API smoke check.")
    parser.add_argument("--rows", default=240, type=int, help="Training rows to generate.")
    parser.add_argument("--random-state", default=42, type=int)
    parser.add_argument("--no-auto-install", action="store_true", help="Fail instead of installing missing Python packages.")
    parser.add_argument("--restart-backend", action="store_true", help="Restart the backend after training the model.")
    parser.add_argument("--skip-api-check", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.chdir(ROOT)
    load_dotenv()
    ensure_dependencies(auto_install=not args.no_auto_install)
    generate_training_seed(rows=args.rows, random_state=args.random_state)
    train_demo_model(random_state=args.random_state)
    ensure_database_auth()
    apply_migrations()
    insert_demo_data()
    restart_backend(restart=args.restart_backend)
    api_check(skip=args.skip_api_check)
    print("MERO demo bootstrap completed.")


if __name__ == "__main__":
    main()
