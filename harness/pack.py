import hashlib
import json
from typing import Any

from harness.models import RunManifest


def compute_result_sha256(
    as_of: str,
    input_sha256: str,
    mapping_version: str,
    ontology_version: str,
    profile: str,
    query_version: str,
    result: dict[str, Any],
) -> str:
    """Computes deterministic result_sha256 over normalized canonical JSON payload."""
    payload = {
        "as_of": as_of,
        "input_sha256": input_sha256,
        "mapping_version": mapping_version,
        "ontology_version": ontology_version,
        "profile": profile,
        "query_version": query_version,
        "result": result,
    }
    canonical_bytes = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical_bytes).hexdigest()


def build_evidence_pack(
    manifest: RunManifest,
    profile: str,
    result: dict[str, Any],
) -> dict[str, Any]:
    """Builds standard evidence pack JSON without rating or pricing fields."""
    pack = manifest.to_dict()
    pack["profile"] = profile
    pack["result"] = result
    return pack
