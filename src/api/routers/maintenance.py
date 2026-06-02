from __future__ import annotations

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import MaintenanceLogCreate, MaintenanceLogItem, MaintenanceLogResponse
from ..security import require_basic_auth


router = APIRouter(dependencies=[Depends(require_basic_auth)])


@router.get("/maintenance-logs", response_model=MaintenanceLogResponse)
def list_maintenance_logs(
    equipment_id: UUID | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
) -> MaintenanceLogResponse:
    query = """
        SELECT maintenance_log_id, equipment_id, reported_at, operator_state,
               failure_code, free_text_observation, created_at
        FROM maintenance_logs
    """
    params: dict[str, object] = {"limit": limit}
    if equipment_id is not None:
        query += " WHERE equipment_id = :equipment_id"
        params["equipment_id"] = equipment_id
    query += " ORDER BY reported_at DESC LIMIT :limit"

    rows = db.execute(text(query), params).mappings().all()
    return MaintenanceLogResponse(items=list(rows))


@router.post(
    "/maintenance-logs",
    response_model=MaintenanceLogItem,
    status_code=status.HTTP_201_CREATED,
)
def create_maintenance_log(
    payload: MaintenanceLogCreate,
    db: Session = Depends(get_db),
) -> MaintenanceLogItem:
    equipment_exists = db.execute(
        text("SELECT 1 FROM equipment WHERE equipment_id = :equipment_id"),
        {"equipment_id": payload.equipment_id},
    ).first()
    if equipment_exists is None:
        raise HTTPException(status_code=404, detail="Equipment not found")

    if payload.failure_code is not None:
        failure_exists = db.execute(
            text("SELECT 1 FROM failure_catalog WHERE failure_code = :failure_code AND is_active = true"),
            {"failure_code": payload.failure_code},
        ).first()
        if failure_exists is None:
            raise HTTPException(status_code=400, detail="Failure code is not active or does not exist")

    try:
        row = db.execute(
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
                RETURNING maintenance_log_id, equipment_id, reported_at, operator_state,
                          failure_code, free_text_observation, created_at
                """
            ),
            {
                "maintenance_log_id": uuid4(),
                "equipment_id": payload.equipment_id,
                "reported_at": payload.reported_at,
                "operator_state": payload.operator_state,
                "failure_code": payload.failure_code,
                "free_text_observation": payload.free_text_observation,
            },
        ).mappings().one()
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail="Maintenance log could not be created") from exc

    return MaintenanceLogItem(**row)

