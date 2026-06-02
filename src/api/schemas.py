from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class AssetHierarchyItem(BaseModel):
    tenant_id: UUID
    plant_id: UUID
    plant_code: str
    line_id: UUID
    line_code: str
    cell_id: UUID
    cell_code: str
    equipment_id: UUID
    equipment_code: str
    equipment_class: str
    last_known_state: str
    last_state_updated_at: datetime


class AssetHierarchyResponse(BaseModel):
    items: list[AssetHierarchyItem]


class EquipmentDetail(BaseModel):
    equipment_id: UUID
    cell_id: UUID
    equipment_code: str
    equipment_name: str
    equipment_class: str
    manufacturer: str | None = None
    model: str | None = None
    serial_number: str | None = None
    installed_at: date | None = None
    last_known_state: str
    last_state_updated_at: datetime


class FailureCatalogItem(BaseModel):
    failure_code: str
    failure_category: str
    failure_mode: str
    iso14224_reference: str | None = None
    is_active: bool


class FailureCatalogResponse(BaseModel):
    items: list[FailureCatalogItem]


class MaintenanceLogCreate(BaseModel):
    equipment_id: UUID
    reported_at: datetime
    operator_state: str = Field(min_length=1, max_length=80)
    failure_code: str | None = Field(default=None, max_length=120)
    free_text_observation: str | None = Field(default=None, max_length=4000)


class MaintenanceLogItem(MaintenanceLogCreate):
    maintenance_log_id: UUID
    created_at: datetime


class MaintenanceLogResponse(BaseModel):
    items: list[MaintenanceLogItem]


class SensorObservationCreate(BaseModel):
    equipment_id: UUID
    observed_at: datetime
    temperature_c: float | None = None
    vibration_mm_s: float | None = None
    pressure_bar: float | None = None
    rpm: float | None = None
    operating_hours: float | None = None
    load_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    sensor_quality: str = Field(default="unknown", min_length=1, max_length=80)


class SensorObservationItem(SensorObservationCreate):
    observation_id: UUID
    created_at: datetime


class SensorObservationResponse(BaseModel):
    items: list[SensorObservationItem]


class DiscrepancyFindingItem(BaseModel):
    finding_id: UUID
    observation_id: UUID
    threshold_id: UUID
    variable_name: str
    observed_value: float
    expected_min: float | None = None
    expected_max: float | None = None
    severity: str
    detected_at: datetime


class DiscrepancyAuditResponse(BaseModel):
    observation_id: UUID
    findings: list[DiscrepancyFindingItem]


class RiskPredictionRequest(BaseModel):
    equipment_id: UUID
    observed_at: datetime
    features: dict[str, Any] = Field(min_length=1)


class RiskPredictionResponse(BaseModel):
    equipment_id: UUID
    observed_at: datetime
    risk_label: str
    risk_score: float = Field(ge=0.0, le=1.0)
    model_version: str
    feature_count: int = Field(ge=1)
