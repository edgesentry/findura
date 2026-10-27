# 公開様式と合成 CSV 列の対応表（S2）

**位置づけ**: 日本およびシンガポールの公開点検様式の欄構造から、合成テストデータ（`synthetic_inspections.csv`）の列を導出した根拠資料。
**方針**:
1. 本番の制度対応の確定ではなく、合成レコードのためのマッピングである。
2. 個人名は一切含めず、資格や役割を示す記号（`ROLE-FE-01`, `ROLE-PE-01` 等）にとどめる。
3. 建物および設備の識別子は `bldg-synth-` および `asset-synth-` の接頭辞を付与する。
4. 金額や保険金の統計数値は一切含まない。

---

## 1. 対象とする公開様式

| 略称 | 正式名称 | 発行元 / 根拠法令 |
| :--- | :--- | :--- |
| **消防庁点検** | 消防用設備等（特殊消防用設備等）点検結果報告書 | 総務省消防庁 / 消防法第17条の3の3 |
| **建基法12条** | 定期調査報告書・定期検査報告書（特定建築設備等） | 国土交通省 / 建築基準法第12条第1項・第3項 |
| **SCDF FC** | Fire Certificate Annual Inspection & Renewal Form | シンガポール民間防衛庁（SCDF）/ Fire Safety Act (Cap 109A) |

---

## 2. 公開様式の欄と合成 CSV 列の対応一覧

| 合成CSV列名 | 意味・コアプロパティ | 消防庁 点検結果報告書 | 建築基準法12条 定期報告 | SCDF Fire Certificate Form |
| :--- | :--- | :--- | :--- | :--- |
| `row_id` | 行識別子（テスト検証用） | - | - | - |
| `record_type` | レコード種別 (`finding` / `detection`) | 点検記録 / 遠隔警報区別 | 調査結果表 / 監視記録 | Inspection Record / Alarm Event |
| `asset_and_building` | `insp:assetKey` \| `insp:buildingKey` | 防火対象物の所在地・名称、設備種類 | 建築物名称、調査対象設備（非常電源等） | Building Name / Fire Safety Works Ref |
| `inspection_id` | `insp:inspectionKey` | 報告書管理番号 | 報告書番号 | FC Submission Reference No. |
| `inspection_date` | `insp:conductedOn` | 点検年月日 | 調査・検査年月日 | Date of Inspection |
| `inspection_kind` | `insp:inspectionKind` | 点検種別（機器点検 / 総合点検） | 定期調査 / 建築設備定期検査 | Annual PE FC Inspection |
| `inspector_role` | `insp:conductedBy` | 点検実施者（消防設備士/点検資格者記号） | 調査者資格者証番号記号 | Professional Engineer (`ROLE-PE-01`) |
| `finding_id` | `insp:findingKey` | 不良箇所・指摘番号 | 要是正・指摘事項番号 | Defect Item No. |
| `defect_text` | `insp:statement` | 不良内容（電気火災原因・防火設備未維持等） | 判定・指摘の内容 | Nature of Non-Compliance / Defect |
| `found_date` | `insp:foundOn` | 点検年月日（指摘確認日） | 調査日 | Date Defect Identified |
| `due_date` | `insp:dueOn` | 改修予定年月日 | 是正・改修予定時期 | Target Rectification Date |
| `status` | `insp:completed` (`open` / `done`) | 措置状況（未改修 / 改修済） | 是正状況（未 / 済） | Status (`open` / `done`) |
| `completion_date` | `insp:completedOn` | 改修完了年月日 | 改善完了年月日 | Date Rectified |
| `detection_id` | `insp:detectionKey` | （スマート保安 漏電受信記録ID） | （負荷・過熱監視警報ID） | （DECAMS Fire Alarm Signal ID） |
| `detected_date` | `insp:detectedOn` | （警報受信年月日） | （検知年月日） | （Date of Alarm Signal） |
