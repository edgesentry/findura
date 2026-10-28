"""Resource resolution for Findura package assets.

Handles resolving schemas, SQL queries, profile YAMLs, mappings, and fixtures
whether running from an installed wheel (package data under `harness/`) or from
an editable repository checkout.
"""

from pathlib import Path


def get_resource_path(relative_path: str | Path) -> Path:
    """Resolve a resource path relative to the package or repository root.

    Checks:
    1. Inside the `harness` package directory (installed wheel layout).
    2. At the repository root (editable checkout layout).
    """
    rel = Path(relative_path)

    # 1. Check under harness package directory (installed wheel)
    pkg_path = Path(__file__).resolve().parent / rel
    if pkg_path.exists():
        return pkg_path

    # 2. Check repository root (editable git checkout)
    repo_path = Path(__file__).resolve().parent.parent / rel
    if repo_path.exists():
        return repo_path

    # Fallback to package path if neither exists
    return pkg_path


def get_schema_dir() -> Path:
    """Return path to schema directory containing tables.sql and JSON Schemas."""
    return get_resource_path("schema")


def get_tables_sql_path() -> Path:
    """Return path to tables.sql."""
    return get_resource_path("schema/tables.sql")


def get_profile_dir(profile_name: str = "insurer") -> Path:
    """Return path to profile directory."""
    return get_resource_path(f"profiles/{profile_name}")


def get_default_mapping_path() -> Path:
    """Return path to default synthetic mapping YAML."""
    return get_resource_path("mappings/sources/source_csv_synthetic.yaml")


def get_default_fixture_path() -> Path:
    """Return path to default synthetic inspections CSV."""
    return get_resource_path("fixtures/synthetic/synthetic_inspections.csv")
