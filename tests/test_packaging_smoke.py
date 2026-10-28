"""Smoke test verifying package asset bundling and runtime resolution."""

import shutil
import subprocess
import zipfile
from pathlib import Path

from harness.db import init_db
from harness.query import run_insurer_query
from harness.resources import (
    get_default_fixture_path,
    get_default_mapping_path,
    get_profile_dir,
    get_resource_path,
    get_schema_dir,
    get_tables_sql_path,
)


def test_resource_helpers_resolve_existing_files():
    """Verify all resource resolver helper functions locate valid assets."""
    assert get_tables_sql_path().exists()
    assert get_tables_sql_path().name == "tables.sql"

    assert get_schema_dir().exists()
    assert (get_schema_dir() / "finding_has_deadline.schema.json").exists()

    assert get_profile_dir("insurer").exists()
    assert (get_profile_dir("insurer") / "profile.yaml").exists()

    assert get_default_fixture_path().exists()
    assert get_default_fixture_path().name == "synthetic_inspections.csv"

    assert get_default_mapping_path().exists()
    assert get_default_mapping_path().name == "source_csv_synthetic.yaml"

    assert get_resource_path("queries/insurer_open_findings_v1.sql").exists()
    assert get_resource_path("queries/insurer_completed_remediations_v1.sql").exists()


def test_wheel_contains_all_runtime_assets(tmp_path: Path):
    """Verify built wheel bundles schema, profiles, queries, mappings, and fixtures."""
    repo_root = Path(__file__).resolve().parent.parent
    dist_dir = tmp_path / "dist"
    uv_bin = shutil.which("uv") or "uv"

    subprocess.run(
        [
            uv_bin,
            "build",
            "--wheel",
            "--out-dir",
            str(dist_dir),
        ],
        cwd=repo_root,
        check=True,
        capture_output=True,
    )

    wheel_files = list(dist_dir.glob("*.whl"))
    assert len(wheel_files) == 1
    wheel_path = wheel_files[0]

    with zipfile.ZipFile(wheel_path, "r") as zf:
        namelist = zf.namelist()

        required_assets = [
            "harness/schema/tables.sql",
            "harness/schema/finding_has_deadline.schema.json",
            "harness/schema/completed_remediation_has_date.schema.json",
            "harness/schema/date_implies_completed.schema.json",
            "harness/schema/inspection_has_one_asset.schema.json",
            "harness/schema/no_fabricated_value.schema.json",
            "harness/profiles/insurer/profile.yaml",
            "harness/queries/insurer_open_findings_v1.sql",
            "harness/queries/insurer_completed_remediations_v1.sql",
            "harness/mappings/sources/source_csv_synthetic.yaml",
            "harness/fixtures/synthetic/synthetic_inspections.csv",
        ]

        for asset in required_assets:
            assert asset in namelist, f"Missing bundled asset in wheel: {asset}"

        # Verify wheel METADATA contains enriched discoverability and license fields
        metadata_entries = [
            name for name in namelist if name.endswith(".dist-info/METADATA")
        ]
        assert len(metadata_entries) == 1
        metadata_text = zf.read(metadata_entries[0]).decode("utf-8")
        assert "License-Expression: Apache-2.0" in metadata_text
        assert "Author-email: Yohei Onishi <yohei.onishi11@gmail.com>" in metadata_text
        assert "Keywords: " in metadata_text
        assert (
            "Classifier: License :: OSI Approved :: Apache Software License"
            in metadata_text
        )
        assert "Classifier: Typing :: Typed" in metadata_text


def test_init_db_and_query_via_bundled_resources(db_conn):
    """Verify init_db and run_insurer_query operate using bundled resources."""
    init_db(db_conn)
    result = run_insurer_query(db_conn, as_of="2026-10-27")
    assert "open_findings" in result
    assert "completed_remediations" in result
