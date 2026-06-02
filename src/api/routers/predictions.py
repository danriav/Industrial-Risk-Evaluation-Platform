from __future__ import annotations

from fastapi import APIRouter, Depends

from ..ml import predict_risk
from ..schemas import RiskPredictionRequest, RiskPredictionResponse
from ..security import require_basic_auth


router = APIRouter(dependencies=[Depends(require_basic_auth)])


@router.post("/predictions/risk", response_model=RiskPredictionResponse)
def create_risk_prediction(payload: RiskPredictionRequest) -> RiskPredictionResponse:
    risk_label, risk_score, model_version = predict_risk(payload.features)
    return RiskPredictionResponse(
        equipment_id=payload.equipment_id,
        observed_at=payload.observed_at,
        risk_label=risk_label,
        risk_score=risk_score,
        model_version=model_version,
        feature_count=len(payload.features),
    )
