from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import SensorObservationCreate, SensorObservationItem, SensorObservationResponse
from ..security import require_basic_auth


router = APIRouter(dependencies=[Depends(require_basic_auth)])


@router.get("/sensor-observations", response_model=SensorObservationResponse)
def list_sensor_observations(
    equipment_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> SensorObservationResponse:
    query = """
        SELECT observation_id, equipment_id, observed_at, temperature_c, vibration_mm_s,
               pressure_bar, rpm, operating_hours, load_pct, sensor_quality, created_at
        FROM sensor_observations
    """
    params: dict[str, object] = {"limit": limit}
    if equipment_id is not None:
        query += " WHERE equipment_id = :equipment_id"
        params["equipment_id"] = equipment_id
    query += " ORDER BY observed_at DESC LIMIT :limit"

    rows = db.execute(text(query), params).mappings().all()
    return SensorObservationResponse(items=list(rows))


@router.post(
    "/sensor-observations",
    response_model=SensorObservationItem,
    status_code=status.HTTP_201_CREATED,
)
def create_sensor_observation(
    payload: SensorObservationCreate,
    db: Session = Depends(get_db),
) -> SensorObservationItem:
    equipment_exists = db.execute(
        text("SELECT 1 FROM equipment WHERE equipment_id = :equipment_id"),
        {"equipment_id": payload.equipment_id},
    ).first()
    if equipment_exists is None:
        raise HTTPException(status_code=404, detail="Equipment not found")

    try:
        row = db.execute(
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
                RETURNING observation_id, equipment_id, observed_at, temperature_c,
                          vibration_mm_s, pressure_bar, rpm, operating_hours,
                          load_pct, sensor_quality, created_at
                """
            ),
            {
                "observation_id": uuid4(),
                "equipment_id": payload.equipment_id,
                "observed_at": payload.observed_at,
                "temperature_c": payload.temperature_c,
                "vibration_mm_s": payload.vibration_mm_s,
                "pressure_bar": payload.pressure_bar,
                "rpm": payload.rpm,
                "operating_hours": payload.operating_hours,
                "load_pct": payload.load_pct,
                "sensor_quality": payload.sensor_quality,
            },
        ).mappings().one()
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Sensor observation could not be created") from exc

    return SensorObservationItem(**row)

