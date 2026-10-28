import json
from pathlib import Path

from harness.ingest import ingest_file
from harness.loader import load_records
from harness.normalize import load_mapping, normalize_batch


def test_s1_synthetic_verdicts_match_expected(db_conn, repo_root: Path):
    """S1 Exit Criteria: All 20 synthetic records match expected_verdicts.json.

    Each of the 5 shapes has both accept and quarantine cases.
    """
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"
    mapping_path = (
        repo_root / "mappings" / "sources" / "source_csv_synthetic.yaml"
    )
    expected_path = (
        repo_root / "fixtures" / "synthetic" / "expected_verdicts.json"
    )

    with open(expected_path, "r", encoding="utf-8") as f:
        expected_data = json.load(f)

    expected_map = {item["row_id"]: item for item in expected_data["verdicts"]}

    batch = ingest_file(csv_path, db_conn)
    mapping = load_mapping(mapping_path)
    records = normalize_batch(batch, mapping)

    assert len(records) == 20

    verdicts = load_records(
        records,
        db_conn,
        input_sha256=batch.input_sha256,
        ontology_version="1",
        mapping_version=str(mapping.get("version", "1")),
        schema_dir=repo_root / "schema",
    )

    assert len(verdicts) == 20

    shapes_tested_quarantine = set()
    accepted_count = 0

    for verdict in verdicts:
        exp = expected_map[verdict.row_id]
        if exp["verdict"] == "accept":
            assert verdict.accepted is True, (
                f"{verdict.row_id} expected accept but got quarantine: {verdict.reason}"
            )
            accepted_count += 1
        else:
            assert verdict.accepted is False, (
                f"{verdict.row_id} expected quarantine but got accept"
            )
            assert verdict.violated_shape == exp["violated_shape"], (
                f"{verdict.row_id} shape mismatch: expected {exp['violated_shape']}, got {verdict.violated_shape}"
            )
            shapes_tested_quarantine.add(verdict.violated_shape)

    # 12 accepted, 8 quarantined
    assert accepted_count == 12
    assert len(verdicts) - accepted_count == 8

    # Ensure all 5 shapes were tested for quarantine
    five_shapes = {
        "FindingHasDeadlineShape",
        "CompletedRemediationHasDateShape",
        "DateImpliesCompletedShape",
        "InspectionHasOneAssetShape",
        "NoFabricatedValueShape",
    }
    assert shapes_tested_quarantine == five_shapes


def test_s1_detections_not_in_remediations(db_conn, repo_root: Path):
    """S1: Detections (Requirement 5) must not be treated as remediations or completion."""
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"
    mapping_path = (
        repo_root / "mappings" / "sources" / "source_csv_synthetic.yaml"
    )

    batch = ingest_file(csv_path, db_conn)
    mapping = load_mapping(mapping_path)
    records = normalize_batch(batch, mapping)
    load_records(records, db_conn, input_sha256=batch.input_sha256)

    with db_conn.cursor() as cur:
        # Check detections count
        cur.execute("SELECT COUNT(*) AS cnt FROM detections;")
        det_cnt = cur.fetchone()["cnt"]
        assert det_cnt == 2  # row-11 and row-12

        # Check detections table has no completed / completed_on columns
        cur.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'detections'
            """
        )
        cols = {row["column_name"] for row in cur.fetchall()}
        assert "completed" not in cols
        assert "completed_on" not in cols
