from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas import FailureCatalogResponse
from ..security import require_basic_auth


router = APIRouter(dependencies=[Depends(require_basic_auth)])


@router.get("/failure-catalog", response_model=FailureCatalogResponse)
def list_failure_catalog(db: Session = Depends(get_db)) -> FailureCatalogResponse:
    rows = db.execute(
        text(
            """
            SELECT failure_code, failure_category, failure_mode, iso14224_reference, is_active
            FROM failure_catalog
            WHERE is_active = true
            ORDER BY failure_category, failure_mode
            """
        )
    ).mappings().all()
    return FailureCatalogResponse(items=list(rows))

