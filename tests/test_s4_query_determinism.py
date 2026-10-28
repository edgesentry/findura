from pathlib import Path

from harness.ingest import ingest_file
from harness.loader import load_records
from harness.normalize import load_mapping, normalize_batch
from harness.pack import compute_result_sha256
from harness.query import run_insurer_query


def test_s4_query_determinism_and_overdue_logic(db_conn, repo_root: Path):
    """S4 Exit Criteria: Same input executed twice yields identical result hash.

    due_on == as_of must not be marked overdue.
    due_on < as_of must be marked overdue.
    """
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"
    mapping_path = repo_root / "mappings" / "sources" / "source_csv_synthetic.yaml"

    batch = ingest_file(csv_path, db_conn)
    mapping = load_mapping(mapping_path)
    records = normalize_batch(batch, mapping)
    load_records(records, db_conn, input_sha256=batch.input_sha256)

    as_of = "2026-10-27"

    # Execution 1
    res1 = run_insurer_query(db_conn, as_of=as_of, profile_dir=repo_root)
    hash1 = compute_result_sha256(
        as_of=as_of,
        input_sha256=batch.input_sha256,
        mapping_version="1",
        ontology_version="1",
        profile="insurer",
        query_version="insurer-open-findings-v1",
        result=res1,
    )

    # Execution 2 (independent execution)
    res2 = run_insurer_query(db_conn, as_of=as_of, profile_dir=repo_root)
    hash2 = compute_result_sha256(
        as_of=as_of,
        input_sha256=batch.input_sha256,
        mapping_version="1",
        ontology_version="1",
        profile="insurer",
        query_version="insurer-open-findings-v1",
        result=res2,
    )

    # Identical result hash
    assert hash1 == hash2
    assert res1 == res2

    # Check overdue logic on open_findings
    open_findings = res1["open_findings"]
    assert len(open_findings) == 6

    # finding-synth-03 has due_on == 2026-10-27 -> overdue must be False
    f3 = next(f for f in open_findings if f["finding_id"] == "finding-synth-03")
    assert f3["due_on"] == "2026-10-27"
    assert f3["overdue"] is False

    # finding-synth-01 has due_on == 2026-09-15 -> overdue must be True
    f1 = next(f for f in open_findings if f["finding_id"] == "finding-synth-01")
    assert f1["due_on"] == "2026-09-15"
    assert f1["overdue"] is True

    # Completed remediations
    comp_rems = res1["completed_remediations"]
    assert len(comp_rems) == 4
    for rem in comp_rems:
        assert rem["completed_on"] is not None
        assert rem["overdue"] is False
