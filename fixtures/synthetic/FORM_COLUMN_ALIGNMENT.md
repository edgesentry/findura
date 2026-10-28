# Statutory Form and Synthetic CSV Column Alignment (S2)

**Purpose**: Rationale document deriving the columns of the synthetic test dataset (`synthetic_inspections.csv`) from the structure of statutory inspection forms in Japan and Singapore.  
**Principles**:
1. Mapping designed for synthetic test data verification, not a finalized legal specification for production filing.
2. Contains no personal names; uses role and qualification identifiers (e.g., `ROLE-FE-01`, `ROLE-PE-01`).
3. Prefixes building and asset identifiers with `bldg-synth-` and `asset-synth-`.
4. Strictly excludes monetary amounts, underwriting scores, and insurance loss statistics.

---

## 1. Target Statutory Inspection Forms

| Abbreviation | Formal Title | Issuing Authority / Statutory Basis |
| :--- | :--- | :--- |
| **FDMA Inspection (消防庁点検)** | Fire Defense Equipment Inspection Result Report (消防用設備等（特殊消防用設備等）点検結果報告書) | Fire and Disaster Management Agency (総務省消防庁 / FDMA) / Fire Service Act (消防法) Art. 17-3-3 |
| **Building Standards Act Art. 12 (建基法12条)** | Periodic Survey Report & Periodic Inspection Report for Specified Building Equipment (定期調査報告書・定期検査報告書（特定建築設備等）) | Ministry of Land, Infrastructure, Transport and Tourism (国土交通省 / MLIT) / Building Standards Act (建築基準法) Art. 12, Paras. 1 & 3 |
| **SCDF FC** | Fire Certificate Annual Inspection & Renewal Form | Singapore Civil Defence Force (シンガポール民間防衛庁 / SCDF) / Fire Safety Act (Cap 109A) |

---

## 2. Alignment Between Statutory Form Fields and Synthetic CSV Columns

| Synthetic CSV Column | Meaning & Core Property | FDMA Inspection Result Report (消防庁 点検結果報告書) | Building Standards Act Art. 12 Periodic Report (建築基準法12条 定期報告) | SCDF Fire Certificate Form |
| :--- | :--- | :--- | :--- | :--- |
| `row_id` | Row identifier (for test verification) | - | - | - |
| `record_type` | Record type (`finding` / `detection`) | Inspection finding vs. remote alarm distinction (点検記録 / 遠隔警報区別) | Survey finding vs. monitoring event (調査結果表 / 監視記録) | Inspection Record / Alarm Event |
| `asset_and_building` | `insp:assetKey` \| `insp:buildingKey` | Fire protection property location/name, equipment category (防火対象物の所在地・名称、設備種類) | Building name, target equipment e.g. emergency power (建築物名称、調査対象設備（非常電源等）) | Building Name / Fire Safety Works Ref |
| `inspection_id` | `insp:inspectionKey` | Report control number (報告書管理番号) | Report reference number (報告書番号) | FC Submission Reference No. |
| `inspection_date` | `insp:conductedOn` | Inspection date (点検年月日) | Survey / inspection date (調査・検査年月日) | Date of Inspection |
| `inspection_kind` | `insp:inspectionKind` | Inspection type: apparatus vs. comprehensive (点検種別: 機器点検 / 総合点検) | Periodic survey vs. periodic equipment inspection (定期調査 / 建築設備定期検査) | Annual PE FC Inspection |
| `inspector_role` | `insp:conductedBy` | Inspector role identifier: Fire Defense Equipment Officer / Qualified Person (点検実施者: 消防設備士/点検資格者記号) | Inspector qualification license number symbol (調査者資格者証番号記号) | Professional Engineer (`ROLE-PE-01`) |
| `finding_id` | `insp:findingKey` | Defect item number (不良箇所・指摘番号) | Required remediation item number (要是正・指摘事項番号) | Defect Item No. |
| `defect_text` | `insp:statement` | Description of defect: electrical fire hazard, unmaintained fire equipment, etc. (不良内容: 電気火災原因・防火設備未維持等) | Evaluation / finding statement (判定・指摘の内容) | Nature of Non-Compliance / Defect |
| `found_date` | `insp:foundOn` | Finding identification date (点検年月日（指摘確認日）) | Survey date (調査日) | Date Defect Identified |
| `due_date` | `insp:dueOn` | Target remediation date (改修予定年月日) | Planned remediation date (是正・改修予定時期) | Target Rectification Date |
| `status` | `insp:completed` (`open` / `done`) | Action status: unrectified / rectified (措置状況: 未改修 / 改修済) | Remediation status: pending / done (是正状況: 未 / 済) | Status (`open` / `done`) |
| `completion_date` | `insp:completedOn` | Remediation completion date (改修完了年月日) | Improvement completion date (改善完了年月日) | Date Rectified |
| `detection_id` | `insp:detectionKey` | Smart maintenance ground fault event ID (スマート保安 漏電受信記録ID) | Load/overheating alarm event ID (負荷・過熱監視警報ID) | DECAMS Fire Alarm Signal ID |
| `detected_date` | `insp:detectedOn` | Alarm signal reception date (警報受信年月日) | Detection date (検知年月日) | Date of Alarm Signal |
