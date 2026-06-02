from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from src.ml.validation import (
    MissingThresholdConsensusError,
    VariableThreshold,
    validate_observation_discrepancies,
)

from ..database import get_db
from ..schemas import DiscrepancyAuditResponse, DiscrepancyFindingItem
from ..security import require_basic_auth


router = APIRouter(dependencies=[Depends(require_basic_auth)])

OBSERVATION_VARIABLES = (
    "temperature_c",
    "vibration_mm_s",
    "pressure_bar",
    "rpm",
    "operating_hours",
    "load_pct",
)


@router.post("/discrepancies/audit/{observation_id}", response_model=DiscrepancyAuditResponse)
def audit_observation_discrepancies(
    observation_id: UUID,
    db: Session = Depends(get_db),
) -> DiscrepancyAuditResponse:
    observation = db.execute(
        text(
            """
            SELECT so.observation_id, e.equipment_class, so.temperature_c,
                   so.vibration_mm_s, so.pressure_bar, so.rpm,
                   so.operating_hours, so.load_pct
            FROM sensor_observations so
            JOIN equipment e ON e.equipment_id = so.equipment_id
            WHERE so.observation_id = :observation_id
            """
        ),
        {"observation_id": observation_id},
    ).mappings().first()
    if observation is None:
        raise HTTPException(status_code=404, detail="Sensor observation not found")

    threshold_rows = db.execute(
        text(
            """
            SELECT threshold_id, variable_name, min_value, max_value,
                   max_delta_per_hour, severity
            FROM discrepancy_thresholds
            WHERE equipment_class = :equipment_class
            """
        ),
        {"equipment_class": observation["equipment_class"]},
    ).mappings().all()
    thresholds = {
        row["variable_name"]: VariableThreshold(
            variable_name=row["variable_name"],
            min_value=float(row["min_value"]) if row["min_value"] is not None else None,
            max_value=float(row["max_value"]) if row["max_value"] is not None else None,
            max_delta_per_hour=(
                float(row["max_delta_per_hour"]) if row["max_delta_per_hour"] is not None else None
            ),
            severity=row["severity"],
        )
        for row in threshold_rows
    }
    threshold_ids = {row["variable_name"]: row["threshold_id"] for row in threshold_rows}
    numeric_observation = {name: observation[name] for name in OBSERVATION_VARIABLES}

    try:
        discrepancies = validate_observation_discrepancies(numeric_observation, thresholds)
    except MissingThresholdConsensusError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    try:
        db.execute(
            text("DELETE FROM discrepancy_findings WHERE observation_id = :observation_id"),
            {"observation_id": observation_id},
        )
        for discrepancy in discrepancies:
            threshold = thresholds[discrepancy.variable_name]
            db.execute(
                text(
                    """
                    INSERT INTO discrepancy_findings (
                        finding_id, observation_id, threshold_id, variable_name,
                        observed_value, expected_min, expected_max, severity
                    )
                    VALUES (
                        :finding_id, :observation_id, :threshold_id, :variable_name,
                        :observed_value, :expected_min, :expected_max, :severity
                    )
                    """
                ),
                {
                    "finding_id": uuid4(),
                    "observation_id": observation_id,
                    "threshold_id": threshold_ids[discrepancy.variable_name],
                    "variable_name": discrepancy.variable_name,
                    "observed_value": discrepancy.observed_value,
                    "expected_min": threshold.min_value,
                    "expected_max": threshold.max_value,
                    "severity": discrepancy.severity,
                },
            )
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Discrepancy audit could not be persisted") from exc

    rows = db.execute(
        text(
            """
            SELECT finding_id, observation_id, threshold_id, variable_name,
                   observed_value, expected_min, expected_max, severity, detected_at
            FROM discrepancy_findings
            WHERE observation_id = :observation_id
            ORDER BY severity, variable_name
            """
        ),
        {"observation_id": observation_id},
    ).mappings().all()
    return DiscrepancyAuditResponse(
        observation_id=observation_id,
        findings=[DiscrepancyFindingItem(**row) for row in rows],
    )
