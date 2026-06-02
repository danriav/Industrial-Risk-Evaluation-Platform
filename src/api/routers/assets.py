from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import AssetHierarchyResponse, EquipmentDetail
from ..security import require_basic_auth


router = APIRouter(dependencies=[Depends(require_basic_auth)])


@router.get("/assets/hierarchy", response_model=AssetHierarchyResponse)
def list_asset_hierarchy(
    tenant_id: UUID | None = None,
    db: Session = Depends(get_db),
) -> AssetHierarchyResponse:
    query = """
        SELECT tenant_id, plant_id, plant_code, line_id, line_code, cell_id, cell_code,
               equipment_id, equipment_code, equipment_class, last_known_state,
               last_state_updated_at
        FROM equipment_iso14224_hierarchy
    """
    params: dict[str, object] = {}
    if tenant_id is not None:
        query += " WHERE tenant_id = :tenant_id"
        params["tenant_id"] = tenant_id
    query += " ORDER BY plant_code, line_code, cell_code, equipment_code"

    rows = db.execute(text(query), params).mappings().all()
    return AssetHierarchyResponse(items=list(rows))


@router.get("/equipment/{equipment_id}", response_model=EquipmentDetail)
def get_equipment(
    equipment_id: UUID,
    db: Session = Depends(get_db),
) -> EquipmentDetail:
    row = db.execute(
        text(
            """
            SELECT equipment_id, cell_id, equipment_code, equipment_name, equipment_class,
                   manufacturer, model, serial_number, installed_at, last_known_state,
                   last_state_updated_at
            FROM equipment
            WHERE equipment_id = :equipment_id
            """
        ),
        {"equipment_id": equipment_id},
    ).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Equipment not found")
    return EquipmentDetail(**row)

