from pathlib import Path

from harness.ingest import ingest_file
from harness.loader import load_records
from harness.normalize import load_mapping, normalize_batch


def test_s3_provenance_traceable_for_all_accepted_rows(db_conn, repo_root: Path):
    """S3 Exit Criteria: All accepted rows can be traced back to their source fields."""
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"
    mapping_path = (
        repo_root / "mappings" / "sources" / "source_csv_synthetic.yaml"
    )

    batch = ingest_file(csv_path, db_conn)
    mapping = load_mapping(mapping_path)
    records = normalize_batch(batch, mapping)
    load_records(records, db_conn, input_sha256=batch.input_sha256)

    accepted_findings_count = 0
    with db_conn.cursor() as cur:
        # Check all findings have value_provenance
        cur.execute("SELECT id, finding_key FROM findings;")
        findings = cur.fetchall()
        accepted_findings_count = len(findings)
        assert accepted_findings_count == 10  # 6 open + 4 completed

        for f in findings:
            f_key = f["finding_key"]
            cur.execute(
                """
                SELECT vp.property_name, sf.field_name, sf.field_value, sr.raw_locator
                FROM value_provenance vp
                JOIN source_fields sf ON vp.source_field_id = sf.id
                JOIN source_records sr ON vp.source_record_id = sr.id
                WHERE vp.core_table = 'findings' AND vp.core_id = %s
                """,
                (f_key,),
            )
            prov_rows = cur.fetchall()
            assert len(prov_rows) > 0, (
                f"Finding {f_key} must have traceable provenance."
            )
            for prov in prov_rows:
                assert prov["field_name"] is not None
                assert prov["raw_locator"] is not None


def test_s3_ingest_idempotency(db_conn, repo_root: Path):
    """S3: Re-ingesting the exact same file does not create duplicate raw batches."""
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"

    batch1 = ingest_file(csv_path, db_conn)
    batch2 = ingest_file(csv_path, db_conn)

    assert batch1.input_sha256 == batch2.input_sha256

    with db_conn.cursor() as cur:
        cur.execute(
            "SELECT COUNT(*) AS cnt FROM raw_batches WHERE input_sha256 = %s",
            (batch1.input_sha256,),
        )
        assert cur.fetchone()["cnt"] == 1
