BEGIN;

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id UUID PRIMARY KEY,
    legal_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS plants (
    plant_id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    plant_code TEXT NOT NULL,
    plant_name TEXT NOT NULL,
    last_known_state TEXT NOT NULL DEFAULT 'unknown',
    last_state_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (tenant_id, plant_code)
);

CREATE TABLE IF NOT EXISTS production_lines (
    line_id UUID PRIMARY KEY,
    plant_id UUID NOT NULL REFERENCES plants(plant_id) ON DELETE CASCADE,
    line_code TEXT NOT NULL,
    line_name TEXT NOT NULL,
    last_known_state TEXT NOT NULL DEFAULT 'unknown',
    last_state_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (plant_id, line_code)
);

CREATE TABLE IF NOT EXISTS cells (
    cell_id UUID PRIMARY KEY,
    line_id UUID NOT NULL REFERENCES production_lines(line_id) ON DELETE CASCADE,
    cell_code TEXT NOT NULL,
    cell_name TEXT NOT NULL,
    last_known_state TEXT NOT NULL DEFAULT 'unknown',
    last_state_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (line_id, cell_code)
);

CREATE TABLE IF NOT EXISTS equipment (
    equipment_id UUID PRIMARY KEY,
    cell_id UUID NOT NULL REFERENCES cells(cell_id) ON DELETE CASCADE,
    equipment_code TEXT NOT NULL,
    equipment_name TEXT NOT NULL,
    equipment_class TEXT NOT NULL,
    manufacturer TEXT,
    model TEXT,
    serial_number TEXT,
    installed_at DATE,
    last_known_state TEXT NOT NULL DEFAULT 'unknown',
    last_state_updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (cell_id, equipment_code)
);

CREATE TABLE IF NOT EXISTS failure_catalog (
    failure_code TEXT PRIMARY KEY,
    failure_category TEXT NOT NULL,
    failure_mode TEXT NOT NULL,
    iso14224_reference TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS sensor_observations (
    observation_id UUID PRIMARY KEY,
    equipment_id UUID NOT NULL REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    observed_at TIMESTAMPTZ NOT NULL,
    temperature_c NUMERIC(10, 3),
    vibration_mm_s NUMERIC(10, 3),
    pressure_bar NUMERIC(10, 3),
    rpm NUMERIC(12, 3),
    operating_hours NUMERIC(14, 3),
    load_pct NUMERIC(6, 3),
    sensor_quality TEXT NOT NULL DEFAULT 'unknown',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (equipment_id, observed_at)
);

CREATE INDEX IF NOT EXISTS idx_sensor_observations_equipment_time
    ON sensor_observations (equipment_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS maintenance_logs (
    maintenance_log_id UUID PRIMARY KEY,
    equipment_id UUID NOT NULL REFERENCES equipment(equipment_id) ON DELETE CASCADE,
    reported_at TIMESTAMPTZ NOT NULL,
    operator_state TEXT NOT NULL,
    failure_code TEXT REFERENCES failure_catalog(failure_code),
    free_text_observation TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_maintenance_logs_equipment_time
    ON maintenance_logs (equipment_id, reported_at DESC);

CREATE TABLE IF NOT EXISTS discrepancy_thresholds (
    threshold_id UUID PRIMARY KEY,
    equipment_class TEXT NOT NULL,
    variable_name TEXT NOT NULL,
    min_value NUMERIC(14, 4),
    max_value NUMERIC(14, 4),
    max_delta_per_hour NUMERIC(14, 4),
    severity TEXT NOT NULL CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    rationale TEXT NOT NULL,
    approved_by TEXT NOT NULL,
    approved_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (equipment_class, variable_name)
);

CREATE TABLE IF NOT EXISTS discrepancy_findings (
    finding_id UUID PRIMARY KEY,
    observation_id UUID NOT NULL REFERENCES sensor_observations(observation_id) ON DELETE CASCADE,
    threshold_id UUID NOT NULL REFERENCES discrepancy_thresholds(threshold_id),
    variable_name TEXT NOT NULL,
    observed_value NUMERIC(14, 4) NOT NULL,
    expected_min NUMERIC(14, 4),
    expected_max NUMERIC(14, 4),
    severity TEXT NOT NULL,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE OR REPLACE VIEW equipment_iso14224_hierarchy AS
SELECT
    t.tenant_id,
    p.plant_id,
    p.plant_code,
    l.line_id,
    l.line_code,
    c.cell_id,
    c.cell_code,
    e.equipment_id,
    e.equipment_code,
    e.equipment_class,
    e.last_known_state,
    e.last_state_updated_at
FROM tenants t
JOIN plants p ON p.tenant_id = t.tenant_id
JOIN production_lines l ON l.plant_id = p.plant_id
JOIN cells c ON c.line_id = l.line_id
JOIN equipment e ON e.cell_id = c.cell_id;

COMMIT;
