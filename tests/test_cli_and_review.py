"""Tests for CLI subcommands and ReviewGate stub."""

import json
from pathlib import Path

from harness.cli import main
from harness.resources import get_default_fixture_path
from harness.review import ReviewGateStub


def test_review_gate_stub():
    """Verify ReviewGate stub behavior for Phase 1/2."""
    gate = ReviewGateStub(current_mapping_version="v1")
    approved, ver = gate.review_diff("dummy diff")
    assert not approved
    assert ver == "v1"
    assert gate.list_queue() == []


def test_cli_subcommands(tmp_path: Path, capsys):
    """Verify execution of CLI subcommands review, ingest, normalize, query, and pack."""
    # 1. review
    main(["review"])
    captured = capsys.readouterr()
    assert "ReviewGate" in captured.out

    # 2. ingest
    fixture_csv = str(get_default_fixture_path())
    main(["ingest", fixture_csv])
    captured = capsys.readouterr()
    assert "Ingested:" in captured.out
    assert "input_sha256:" in captured.out

    # 3. normalize
    main(["normalize"])
    captured = capsys.readouterr()
    assert "Normalization & Graph Loading complete:" in captured.out

    # 4. query
    main(["query", "--profile", "insurer", "--as-of", "2026-10-27"])
    captured = capsys.readouterr()
    query_json = json.loads(captured.out)
    assert "open_findings" in query_json

    # 5. pack with --output
    out_file = tmp_path / "evidence_pack.json"
    main(
        [
            "pack",
            "--profile",
            "insurer",
            "--as-of",
            "2026-10-27",
            "--output",
            str(out_file),
        ]
    )
    captured = capsys.readouterr()
    assert out_file.exists()
    pack_data = json.loads(out_file.read_text(encoding="utf-8"))
    assert pack_data["profile"] == "insurer"
    assert pack_data["query_version"] == "insurer-open-findings-v1"
    assert "result_sha256:" in captured.out

    # 6. pack without --output (stdout)
    main(["pack", "--profile", "insurer", "--as-of", "2026-10-27"])
    captured = capsys.readouterr()
    assert "result_sha256" in captured.out
