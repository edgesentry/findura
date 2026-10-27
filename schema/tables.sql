-- Inspectra Core Schema (PostgreSQL / Pattern 3)
-- Version: 1.0.0
-- Defined according to ONTOLOGY_CORE_INSPECTION.md and HARNESS_ARCHITECTURE.md

-- Raw data storage & provenance
CREATE TABLE IF NOT EXISTS raw_batches (
    input_sha256 VARCHAR(64) PRIMARY KEY,
    raw_bytes BYTEA NOT NULL,
    raw_locator TEXT NOT NULL,
    column_names JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS source_records (
    id VARCHAR(64) PRIMARY KEY,
    input_sha256 VARCHAR(64) NOT NULL REFERENCES raw_batches(input_sha256),
    row_index INT NOT NULL,
    raw_locator TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS source_fields (
    id VARCHAR(128) PRIMARY KEY,
    source_record_id VARCHAR(64) NOT NULL REFERENCES source_records(id),
    field_name TEXT NOT NULL,
    field_value TEXT NOT NULL
);

-- Core ontology tables (8 classes equivalent)
-- 1. insp:Building
CREATE TABLE IF NOT EXISTS buildings (
    id SERIAL PRIMARY KEY,
    building_key TEXT UNIQUE NOT NULL
);

-- 2. insp:Asset
CREATE TABLE IF NOT EXISTS assets (
    id SERIAL PRIMARY KEY,
    asset_key TEXT UNIQUE NOT NULL,
    building_id INT NOT NULL REFERENCES buildings(id)
);

-- 3. insp:Inspection
CREATE TABLE IF NOT EXISTS inspections (
    id SERIAL PRIMARY KEY,
    inspection_key TEXT UNIQUE NOT NULL,
    asset_id INT NOT NULL REFERENCES assets(id),
    conducted_on DATE NOT NULL,
    inspection_kind TEXT,
    conducted_by TEXT
);

-- 4. insp:Finding
CREATE TABLE IF NOT EXISTS findings (
    id SERIAL PRIMARY KEY,
    finding_key TEXT UNIQUE NOT NULL,
    inspection_id INT NOT NULL REFERENCES inspections(id),
    statement TEXT NOT NULL,
    found_on DATE NOT NULL
);

-- 5. insp:Deadline
CREATE TABLE IF NOT EXISTS deadlines (
    id SERIAL PRIMARY KEY,
    finding_id INT NOT NULL REFERENCES findings(id),
    due_on DATE NOT NULL,
    CONSTRAINT deadlines_one_per_finding UNIQUE (finding_id)
);

-- 6. insp:Remediation
CREATE TABLE IF NOT EXISTS remediations (
    id SERIAL PRIMARY KEY,
    finding_id INT UNIQUE NOT NULL REFERENCES findings(id),
    completed BOOLEAN NOT NULL,
    completed_on DATE,
    CONSTRAINT completed_date_matches_flag CHECK (
        (completed AND completed_on IS NOT NULL)
        OR ((NOT completed) AND completed_on IS NULL)
    )
);

-- 7. insp:Detection (DetectionIsNotCompletionShape: no completed / completed_on columns)
CREATE TABLE IF NOT EXISTS detections (
    id SERIAL PRIMARY KEY,
    detection_key TEXT UNIQUE NOT NULL,
    asset_id INT NOT NULL REFERENCES assets(id),
    detected_on DATE NOT NULL
);

-- Value Provenance (prov:wasDerivedFrom)
CREATE TABLE IF NOT EXISTS value_provenance (
    id SERIAL PRIMARY KEY,
    core_table TEXT NOT NULL,
    core_id TEXT NOT NULL,
    property_name TEXT NOT NULL,
    source_record_id VARCHAR(64) NOT NULL REFERENCES source_records(id),
    source_field_id VARCHAR(128) NOT NULL REFERENCES source_fields(id),
    source_field_name TEXT NOT NULL,
    source_field_value TEXT NOT NULL
);

-- Quarantine records for constraint violations
CREATE TABLE IF NOT EXISTS quarantine_records (
    id SERIAL PRIMARY KEY,
    input_sha256 VARCHAR(64) NOT NULL,
    ontology_version TEXT NOT NULL,
    mapping_version TEXT NOT NULL,
    violated_shape TEXT NOT NULL,
    reason TEXT NOT NULL,
    rejected_record JSONB NOT NULL,
    run_id TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
