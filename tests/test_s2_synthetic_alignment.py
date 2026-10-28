import csv
from pathlib import Path


def test_s2_alignment_doc_exists_and_covers_columns(repo_root: Path):
    """S2 Exit Criteria: Alignment table between official forms and synthetic CSV exists."""
    doc_path = repo_root / "fixtures" / "synthetic" / "FORM_COLUMN_ALIGNMENT.md"
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"

    assert doc_path.exists(), "FORM_COLUMN_ALIGNMENT.md must exist."

    doc_text = doc_path.read_text(encoding="utf-8")
    assert "消防庁" in doc_text
    assert "建築基準法12条" in doc_text
    assert "Fire Certificate" in doc_text

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)

    # Check each CSV header is documented in FORM_COLUMN_ALIGNMENT.md
    for col in headers:
        assert f"`{col}`" in doc_text, (
            f"CSV column {col} must be documented in alignment doc."
        )


def test_s2_synthetic_rules_compliance(repo_root: Path):
    """S2 Rules: No personal names, no claim amounts, prefixed building/asset keys."""
    csv_path = repo_root / "fixtures" / "synthetic" / "synthetic_inspections.csv"

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 20

    for row in rows:
        # Check prefixes
        asset_building = row.get("asset_and_building", "")
        if "|" in asset_building:
            asset_k, bldg_k = asset_building.split("|")
            if asset_k:
                assert asset_k.startswith("asset-synth-"), (
                    f"Asset key must start with asset-synth-: {asset_k}"
                )
            if bldg_k:
                assert bldg_k.startswith("bldg-synth-"), (
                    f"Building key must start with bldg-synth-: {bldg_k}"
                )

        # Check inspector role is a role code not person name
        inspector = row.get("inspector_role", "")
        if inspector:
            assert inspector.startswith("ROLE-"), (
                f"Inspector should be a role token, got: {inspector}"
            )
