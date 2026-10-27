import uuid
from pathlib import Path

from harness.ingest import ingest_file
from harness.loader import load_records
from harness.models import RunManifest
from harness.normalize import load_mapping, normalize_batch
from harness.pack import build_evidence_pack, compute_result_sha256
from harness.query import run_insurer_query


def test_s6_evidence_pack_regeneration_and_schema(db_conn, repo_root: Path):
    """S6 Exit Criteria:

    Evidence pack contains required manifest fields, no forbidden rating/underwriting fields,
    and the same query result can be regenerated from pack parameters.
    """
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"
    mapping_path = (
        repo_root / "mappings" / "sources" / "source_csv_synthetic.yaml"
    )

    batch = ingest_file(csv_path, db_conn)
    mapping = load_mapping(mapping_path)
    records = normalize_batch(batch, mapping)
    load_records(records, db_conn, input_sha256=batch.input_sha256)

    as_of = "2026-10-27"
    run_id = str(uuid.uuid4())
    profile = "insurer"
    query_version = "insurer-open-findings-v1"

    query_res = run_insurer_query(db_conn, as_of=as_of, profile_dir=repo_root)

    manifest = RunManifest(
        run_id=run_id,
        ontology_version="1",
        mapping_version=str(mapping.get("version", "1")),
        query_version=query_version,
        input_sha256=batch.input_sha256,
        as_of=as_of,
    )

    pack = build_evidence_pack(manifest, profile=profile, result=query_res)

    # Required fields in evidence pack
    assert pack["run_id"] == run_id
    assert pack["ontology_version"] == "1"
    assert pack["mapping_version"] == "1"
    assert pack["query_version"] == query_version
    assert pack["input_sha256"] == batch.input_sha256
    assert pack["as_of"] == as_of
    assert pack["profile"] == "insurer"
    assert "result" in pack

    # Check forbidden underwriting/pricing fields
    forbidden_keys = {
        "rating",
        "rate",
        "discount",
        "premium",
        "underwriting_verdict",
        "claim_amount",
    }
    for k in forbidden_keys:
        assert k not in pack
        assert k not in pack["result"]

    # Regeneration verification: run query using pack's parameters
    regenerated_result = run_insurer_query(
        db_conn, as_of=pack["as_of"], profile_dir=repo_root
    )
    assert regenerated_result == pack["result"]

    # Compute hash over original and regenerated result
    orig_hash = compute_result_sha256(
        as_of=pack["as_of"],
        input_sha256=pack["input_sha256"],
        mapping_version=pack["mapping_version"],
        ontology_version=pack["ontology_version"],
        profile=pack["profile"],
        query_version=pack["query_version"],
        result=pack["result"],
    )

    regen_hash = compute_result_sha256(
        as_of=pack["as_of"],
        input_sha256=pack["input_sha256"],
        mapping_version=pack["mapping_version"],
        ontology_version=pack["ontology_version"],
        profile=pack["profile"],
        query_version=pack["query_version"],
        result=regenerated_result,
    )

    assert orig_hash == regen_hash
