# Findura

**Findura** is an open-source (Apache-2.0) core implementation of a common inspection ontology and deterministic agent harness for operational building inspection and remediation records.

Prior to property & casualty (fire and property insurance) renewals, Findura serves as a neutral data integration layer without replacing existing field inspection software or frontends, providing evidence packs for open findings, overdue deadlines, and completed remediations with complete reproducibility.

---

## Key Features (Phase 1: Minimal Deterministic Core and Insurer Profile MVP)

- **Common Inspection Ontology (8 Core Classes & 5 Shapes)**:
  - `Building`, `Asset`, `Inspection`, `Finding`, `Deadline`, `Remediation`, `Detection`, `SourceRecord`
  - 5 Shape Constraints (`FindingHasDeadlineShape`, `CompletedRemediationHasDateShape`, `DateImpliesCompletedShape`, `InspectionHasOneAssetShape`, `NoFabricatedValueShape`)
  - Detailed formal specification, statutory origins, and validity justification documented in [docs/ONTOLOGY_SPECIFICATION.md](docs/ONTOLOGY_SPECIFICATION.md).
- **Deterministic Harness**:
  - Ingestion (`ingest`): Raw-byte SHA-256 ingestion with property-level provenance tracking
  - Normalization (`normalize`): Pure-function transformation driven by approved mapping YAML (v0)
  - Database Loading (`loader`): JSON Schema validation with canonical core table storage vs. quarantined violations (`quarantine_records`)
  - Query (`query`): Parameter-bound deterministic SQL based on reference date `as_of` for open findings, overdues, and completed remediations
  - Evidence Pack (`pack`): Generation of pre-renewal findings manifest with embedded canonical JSON `result_sha256`
- **Reproducibility Guarantee**: Identical `result_sha256` guaranteed across repeated runs given the same inputs, version, and reference date (`as_of`).
- **Point-in-Time Query Semantics**:
  - `open_findings`: Retrieves findings identified on or before `as_of` that remained unresolved at that reference point (uncompleted or completed after `as_of`).
  - `completed_remediations`: Retrieves only remediations confirmed completed on or before `as_of`.
  - Prohibits all wall-clock functions (`NOW()`, `CURRENT_DATE`, `CURRENT_TIMESTAMP`, `LOCALTIME`, `LOCALTIMESTAMP`) to ensure historical point-in-time states can be deterministically reproduced.

---

## Directory Structure

```text
findura/
├── docs/                   # Core ontology specifications and architecture rationale
├── schema/                 # Database schema (tables.sql) and 5 JSON Schema shapes
├── ontology/               # Ontology definitions (RDF/SHACL vocabularies planned for Phase 3)
├── mappings/sources/       # Mapping definitions v0 (source_csv_synthetic.yaml)
├── queries/                # Deterministic query SQL (insurer-open-findings-v1, completed-remediations-v1)
├── profiles/insurer/       # Insurer profile skeleton (profile.yaml)
├── fixtures/synthetic/     # Statutory form alignment table, 20 synthetic records, and expected verdicts
├── harness/                # Agent harness implementation (ingest, normalize, loader, query, pack, cli)
└── tests/                  # Automated test suite for S1–S4, S6 acceptance criteria
```

---

## Setup and Execution

### 1. Start PostgreSQL

```bash
docker compose up -d
```

### 2. Install Dependencies

```bash
uv sync
```

### 3. Code Quality and Tests

```bash
# Formatting check
uv run ruff format --check .

# Linting
uv run ruff check .

# Static type checking
uv run mypy

# Automated tests
uv run pytest -v
```

### 4. CLI Execution Examples

When installed via `pip` or `uv`, the package bundles all default schemas, queries, mappings, and synthetic fixtures:

```bash
# Ingest raw source data (file argument is resolved relative to CWD)
uv run harness ingest fixtures/synthetic/synthetic_inspections.csv

# Normalize and load (defaults to bundled synthetic fixture and mapping; --file and --mapping resolve relative to CWD)
uv run harness normalize

# Query insurer profile (reference date: 2026-10-27)
uv run harness query --profile insurer --as-of 2026-10-27

# Build evidence pack (output file written relative to CWD)
uv run harness pack --profile insurer --as-of 2026-10-27 --output evidence_pack.json
```

> **Note on CLI paths**: User-supplied path flags (`--file`, `--mapping`, `--output`) resolve relative to the current working directory. If omitted, `normalize` and `pack` automatically fall back to the package-bundled synthetic fixtures and mappings.

---

## License

[Apache License 2.0](LICENSE)
