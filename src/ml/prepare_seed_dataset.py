from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path


EQUIPMENT_CLASSES = ("centrifugal_pump", "compressor", "conveyor", "mixer")
SENSOR_QUALITIES = ("good", "degraded", "unknown")


def classify_risk(
    temperature_c: float,
    vibration_mm_s: float,
    pressure_bar: float,
    load_pct: float,
    sensor_quality: str,
) -> str:
    if temperature_c >= 82 or vibration_mm_s >= 7.0 or pressure_bar >= 12.2:
        return "high"
    if temperature_c >= 76 or vibration_mm_s >= 5.5 or load_pct >= 91 or sensor_quality == "degraded":
        return "medium"
    return "low"


def build_rows(row_count: int, random_state: int) -> list[dict[str, object]]:
    rng = random.Random(random_state)
    rows: list[dict[str, object]] = []

    for index in range(row_count):
        equipment_class = EQUIPMENT_CLASSES[index % len(EQUIPMENT_CLASSES)]
        phase = index % 12
        sensor_quality = SENSOR_QUALITIES[(index // 7) % len(SENSOR_QUALITIES)]

        base_temperature = {
            "centrifugal_pump": 68,
            "compressor": 74,
            "conveyor": 58,
            "mixer": 63,
        }[equipment_class]
        base_vibration = {
            "centrifugal_pump": 3.2,
            "compressor": 4.1,
            "conveyor": 2.4,
            "mixer": 3.7,
        }[equipment_class]
        base_pressure = {
            "centrifugal_pump": 8.2,
            "compressor": 10.4,
            "conveyor": 3.1,
            "mixer": 5.6,
        }[equipment_class]

        stress = 0.0
        if phase in (7, 8, 9):
            stress = 1.0
        elif phase in (10, 11):
            stress = 2.0

        temperature_c = base_temperature + stress * 8 + rng.uniform(-3.5, 3.5)
        vibration_mm_s = base_vibration + stress * 1.9 + rng.uniform(-0.55, 0.65)
        pressure_bar = base_pressure + stress * 1.25 + rng.uniform(-0.7, 0.8)
        rpm = {
            "centrifugal_pump": 1780,
            "compressor": 3600,
            "conveyor": 900,
            "mixer": 1250,
        }[equipment_class] + rng.uniform(-90, 90)
        load_pct = 63 + stress * 15 + rng.uniform(-8, 9)
        operating_hours = 800 + index * 18 + rng.uniform(-12, 12)

        row = {
            "equipment_class": equipment_class,
            "sensor_quality": sensor_quality,
            "temperature_c": round(temperature_c, 3),
            "vibration_mm_s": round(vibration_mm_s, 3),
            "pressure_bar": round(pressure_bar, 3),
            "rpm": round(rpm, 3),
            "operating_hours": round(operating_hours, 3),
            "load_pct": round(load_pct, 3),
            "failure_label": classify_risk(
                temperature_c,
                vibration_mm_s,
                pressure_bar,
                load_pct,
                sensor_quality,
            ),
        }

        if index % 37 == 0:
            row["temperature_c"] = ""
        if index % 41 == 0:
            row["pressure_bar"] = ""

        rows.append(row)

    return rows


def write_dataset(output_path: Path, row_count: int, random_state: int) -> None:
    rows = build_rows(row_count=row_count, random_state=random_state)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as dataset:
        writer = csv.DictWriter(dataset, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Create the initial MERO training dataset.")
    parser.add_argument("--output", default=Path("data/training_seed.csv"), type=Path)
    parser.add_argument("--rows", default=240, type=int)
    parser.add_argument("--random-state", default=42, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    write_dataset(args.output, args.rows, args.random_state)
