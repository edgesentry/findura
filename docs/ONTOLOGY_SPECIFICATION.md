# Findura Core Ontology Specification

**Version**: 0.1.0 (Phase 1: Minimal Deterministic Core)  
**Status**: Active implementation (PostgreSQL DDL & JSON Schema)  
**Provisional Token**: `insp:`  
**Provisional URN**: `urn:insp:provisional:`  

---

## 1. Scope & System Architecture

Findura provides a common, neutral inspection ontology and deterministic agent harness for operational building compliance, defect tracking, and insurance renewal verification.

Rather than replacing existing field inspection software or imposing monolithic building models, Findura acts as a neutral data integration layer. It standardizes heterogeneous inspection and monitoring logs into a minimal, factual representation required for property and casualty (fire and property insurance) renewals.

The lifecycle consists of a two-stage deterministic pipeline:
1. **Raw Ingestion & Provenance**: Raw bytes are captured with SHA-256 hashes in `source_records`, and individual raw column values are stored in `source_fields`.
2. **Deterministic Normalization & Validation**: Approved mapping YAML transforms source records into core entities. Every entity attribute maintains property-level provenance (`prov:wasDerivedFrom`) pointing to its source field. Conforming records are loaded into core tables, while records violating any of the 5 shape constraints are isolated in `quarantine_records`.

---

## 2. Core Classes (8 Classes)

The core ontology comprises 8 classes designed around an event-and-finding lifecycle:

| Class | Description | Structural Role |
| :--- | :--- | :--- |
| `insp:Building` | The physical building or facility structure where assets reside. | Root physical boundary (`insp:buildingKey`). |
| `insp:Asset` | Physical equipment or structural component inspected. Unifies electrical equipment and fire protection equipment without subclass proliferation. | Belongs to a building (`insp:locatedIn`). |
| `insp:Inspection` | An official inspection event conducted at a specific point in time by a qualified inspector. | Exactly one target asset (`insp:inspectedAsset`). |
| `insp:Finding` | A specific non-conformance, defect, or maintenance issue identified during an inspection. | Discovered during an inspection (`insp:foundDuring`). |
| `insp:Deadline` | The mandatory target rectification date by which a finding must be resolved. | Bounds exactly one finding (`insp:bounds`). |
| `insp:Remediation` | The corrective action resolving a finding, recording completion status and completion date. | Remediates exactly one finding (`insp:remediates`). |
| `insp:Detection` | Continuous monitoring alerts (e.g. electrical leakage, thermal spikes). Not an inspection finding and not a completed remediation. | Concerns an asset (`insp:concerns`). |
| `insp:SourceRecord` | Raw data provenance tracking: immutable raw byte SHA-256 hash and locator. | Root of lineage (`insp:sha256`). Accompanied by `insp:SourceField`. |

---

## 3. Property Matrix & Shape Constraints

All entities maintain strict cardinality and data typing:

| Class | Property | Cardinality | Data Type / Target | Constraint / Shape |
| :--- | :--- | :--- | :--- | :--- |
| `insp:Building` | `insp:buildingKey` | 1 | `xsd:string` | Natural or synthetic key (`bldg-synth-*`) |
| `insp:Asset` | `insp:assetKey` | 1 | `xsd:string` | Unique asset identifier |
| `insp:Asset` | `insp:locatedIn` | 1 | `insp:Building` | Foreign key to building |
| `insp:Inspection` | `insp:inspectionKey` | 1 | `xsd:string` | Unique inspection report ID |
| `insp:Inspection` | `insp:inspectedAsset` | 1 | `insp:Asset` | `InspectionHasOneAssetShape` (exactly 1 asset) |
| `insp:Inspection` | `insp:conductedOn` | 1 | `xsd:date` | Date inspection was carried out |
| `insp:Inspection` | `insp:inspectionKind` | 0..1 | `xsd:string` | Inspection category (e.g., apparatus vs. comprehensive) |
| `insp:Inspection` | `insp:conductedBy` | 0..1 | `xsd:string` | Inspector qualification/role identifier |
| `insp:Finding` | `insp:findingKey` | 1 | `xsd:string` | Unique finding identifier |
| `insp:Finding` | `insp:foundDuring` | 1 | `insp:Inspection` | Link to parent inspection |
| `insp:Finding` | `insp:statement` | 1 | `xsd:string` | Verbatim finding statement / description |
| `insp:Finding` | `insp:foundOn` | 1 | `xsd:date` | Date finding was confirmed |
| `insp:Finding` | `insp:hasDeadline` | 1 | `insp:Deadline` | `FindingHasDeadlineShape` (exactly 1 deadline) |
| `insp:Deadline` | `insp:dueOn` | 1 | `xsd:date` | Scheduled remediation target date |
| `insp:Deadline` | `insp:bounds` | 1 | `insp:Finding` | Target finding |
| `insp:Remediation` | `insp:remediates` | 1 | `insp:Finding` | Target finding |
| `insp:Remediation` | `insp:completed` | 1 | `xsd:boolean` | Whether remediation is completed |
| `insp:Remediation` | `insp:completedOn` | 0..1 | `xsd:date` | `CompletedRemediationHasDateShape` & `DateImpliesCompletedShape` |
| `insp:Detection` | `insp:detectionKey` | 1 | `xsd:string` | Sensor alert event identifier |
| `insp:Detection` | `insp:concerns` | 1 | `insp:Asset` | Target equipment monitored |
| `insp:Detection` | `insp:detectedOn` | 1 | `xsd:date` | Alert trigger date (never has `completedOn`) |
| `insp:SourceRecord` | `insp:sha256` | 1 | `xsd:string` | SHA-256 of raw ingested bytes |
| `insp:SourceField` | `insp:fieldName` | 1 | `xsd:string` | Raw column/field name |
| `insp:SourceField` | `insp:fieldValue` | 1 | `xsd:string` | Raw unnormalized string value |

Every normalized attribute in core tables links to `insp:SourceField` via `prov:wasDerivedFrom` recorded in `value_provenance`.

---

## 4. The 5 Core Shape Constraints

Findura enforces five core shape constraints across all ingestion channels:

1. **`FindingHasDeadlineShape`**:
   - Every finding MUST have an associated deadline with a valid target date (`due_on`).
   - If a statutory inspection form omits a scheduled rectification date, the record violates this shape and is routed to quarantine.
2. **`CompletedRemediationHasDateShape`**:
   - If remediation status is completed (`completed = TRUE`), the completion date (`completed_on`) MUST be present.
3. **`DateImpliesCompletedShape`**:
   - If a completion date (`completed_on`) is present, the remediation status MUST be completed (`completed = TRUE`).
4. **`InspectionHasOneAssetShape`**:
   - Each inspection event record MUST correspond to exactly one physical asset. Multi-asset reports must be decomposed using composite keys before core loading.
5. **`NoFabricatedValueShape`**:
   - Every core value must be deterministically derivable from an identifiable source field via an approved transformation. Values not present in raw inputs or synthetic hallucinations are strictly prohibited.

---

## 5. Origins & Derivation

The classes, attributes, and constraints are derived from three foundational sources:

### 1. Statutory Inspection Frameworks (Japan and Singapore)
- **Japan - Fire Service Act (消防法) Art. 17-3-3**:
  - *Form*: Fire Defense Equipment Inspection Result Report (消防用設備等（特殊消防用設備等）点検結果報告書), Fire and Disaster Management Agency (総務省消防庁 / FDMA).
  - *Derivation*: Distinguishes apparatus inspections (機器点検) and comprehensive functional inspections (総合点検), defect notification items, and scheduled rectification dates.
- **Japan - Building Standards Act (建築基準法) Art. 12, Paras. 1 & 3**:
  - *Form*: Periodic Survey Report & Periodic Inspection Report for Specified Building Equipment (定期調査報告書・定期検査報告書（特定建築設備等）), Ministry of Land, Infrastructure, Transport and Tourism (国土交通省 / MLIT).
  - *Derivation*: Emergency power supplies, fire ventilation, and compartmentalization inspection records.
- **Japan - Smart Electrical Safety (スマート保安)**:
  - *Derivation*: Continuous insulation resistance and leakage current monitoring signals, mapped to `insp:Detection`.
- **Singapore - Fire Safety Act (Cap 109A)**:
  - *Form*: Fire Certificate Annual Inspection & Renewal Form, Singapore Civil Defence Force (シンガポール民間防衛庁 / SCDF) and Professional Engineer (PE) annual renewal forms.
  - *Derivation*: Defect itemization, annual renewal cycle verification, and notice of non-compliance tracking.

### 2. W3C Open Standards
- **W3C PROV-O**:
  - Provides the foundation for data lineage (`prov:wasDerivedFrom`). Every core property points back to the exact `SourceField` and `SourceRecord` hash.
- **W3C SHACL / JSON Schema**:
  - The 5 shape constraints are modeled after SHACL node and property shapes, implemented in Phase 1 via JSON Schema (`schema/*.schema.json`).

### 3. Property & Casualty Insurance Underwriting Realities
- Insurers during renewal require proof of risk maintenance: **"When was it inspected, who conducted it, what defects were found, what was the deadline, and when was it verified fixed?"**
- Findura extracts this minimal factual kernel without exposing private insurer rating algorithms or forcing building operators to change their inspection tools.

---

## 6. Design Rationale & Validity Justification

### Why a Minimal 8-Class Core?
Industry ontologies like IFC/BIM, Brick Schema, or RealEstateCore contain thousands of entity types detailing geometric and spatial relationships. While valuable for construction design, they are excessive and unmanageable for operational risk underwriting. Findura focuses strictly on the **temporal and causal lifecycle of compliance defects**, resulting in an 8-class core that is deterministic, auditable, and easily mapped across disparate tools.

### Zero Hallucination & No Value Fabrication
When real inspection sheets contain missing data (such as blank target completion dates), conventional LLM-based ingestion pipelines often attempt to "fill in the blanks" through plausible inference. In insurance compliance, synthetic estimation constitutes evidentiary fraud. Findura strictly isolates non-conforming records in `quarantine_records` rather than fabricating values, guaranteeing 100% evidentiary validity.

### Strict Separation of Detection from Remediation
Sensors frequently fire intermittent warnings (e.g. temporary current surges). When a sensor returns to normal, it indicates that the threshold is no longer breached—it does **not** indicate that a certified engineer inspected the physical equipment and completed repairs. Findura strictly forbids `insp:Detection` from bearing `completed` or `completed_on` properties.

### Point-in-Time Query Determinism
Insurance underwriting verifies the risk state as of a contract renewal reference date (`as_of`). System wall-clock queries (`NOW()`, `CURRENT_DATE`) produce varying results depending on execution time. Findura binds all temporal queries to explicit `:as_of` parameters, guaranteeing that regenerating an evidence pack years later yields an identical canonical JSON SHA-256 hash (`result_sha256`).
