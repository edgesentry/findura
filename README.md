# Inspectra

**Inspectra** は、運用中建物の点検・是正記録を扱う共通点検オントロジーおよび決定論的エージェントハーネスのオープンソース（Apache-2.0）コア実装です。

損害保険会社（火災保険・財物保険）の更改前に、既存の点検ツール（カミナシ等）の画面を置き換えることなく、中立なデータ連携層として未是正指摘・期限超過・是正完了の証拠パックを完全な再現性をもって提供します。

---

## 主な機能（フェーズ 1：最小決定論コアと損保プロファイル MVP）

- **共通点検オントロジー（8クラス・5制約）**:
  - `Building`, `Asset`, `Inspection`, `Finding`, `Deadline`, `Remediation`, `Detection`, `SourceRecord`
  - 5つの形状制約（`FindingHasDeadlineShape`, `CompletedRemediationHasDateShape`, `DateImpliesCompletedShape`, `InspectionHasOneAssetShape`, `NoFabricatedValueShape`）
- **決定論ハーネス**:
  - 取り込み（`ingest`）: 生バイトの SHA-256 保存と項目の出所保持
  - 正規化（`normalize`）: 承認済みマッピング YAML（v0）による純粋関数変換
  - データベース格納（`loader`）: JSON Schema 検証と正本格納／違反隔離（`quarantine_records`）
  - 照会（`query`）: 基準日 `as_of` に基づく未是正・期限超過・完了の決定論的 SQL
  - 証拠パック（`pack`）: 更改前一覧・マニフェスト・`result_sha256` の生成
- **再現性**: 同一入力・同一版・同一基準日に対して、二回実行しても完全に同一の `result_sha256` を保証。
- **点時間（Point-in-time）照会**:
  - `open_findings`: 基準日 `as_of` 以前に発見され、`as_of` 時点で未是正（未完了または `as_of` より後に是正完了）の指摘を抽出。
  - `completed_remediations`: 基準日 `as_of` 以前に完了した是正のみを抽出。
  - `NOW()` / `CURRENT_DATE` 等の壁時計関数は一切排除され、過去の任意の基準日における状態を決定論的に再現。

---

## ディレクトリ構成

```text
inspectra/
├── schema/                 # テーブル定義（tables.sql）および 5つの JSON Schema
├── ontology/               # オントロジー定義（フェーズ 3 で RDF/SHACL を配置）
├── mappings/sources/       # マッピング記法 v0 (source_csv_synthetic.yaml)
├── queries/                # 決定論的照会 SQL (insurer-open-findings-v1)
├── profiles/insurer/       # 損保向けプロファイル骨格 (profile.yaml)
├── fixtures/synthetic/     # 公開様式対応表と合成データ 20件、期待判定表
├── harness/                # エージェントハーネス実装 (ingest, normalize, loader, query, pack, cli)
└── tests/                  # S1〜S4, S6 の完了判定自動テストスイート
```

---

## セットアップと実行

### 1. PostgreSQL の起動

```bash
docker compose up -d
```

### 2. 依存関係のインストール

```bash
uv sync
```

### 3. テストの実行

```bash
uv run pytest -v
```

### 4. CLI の実行例

```bash
# 取り込み
uv run harness ingest fixtures/synthetic/synthetic_inspections.csv

# 正規化と格納（適合は正本へ、違反は隔離表へ）
uv run harness normalize --mapping mappings/sources/source_csv_synthetic.yaml

# 損保プロファイルの照会（基準日 2026-10-27）
uv run harness query --profile insurer --as-of 2026-10-27

# 証拠パックの生成
uv run harness pack --profile insurer --as-of 2026-10-27 --output evidence_pack.json
```

---

## ライセンス

[Apache License 2.0](LICENSE)
