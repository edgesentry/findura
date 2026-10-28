from dataclasses import dataclass, field
from typing import Any


@dataclass
class RawBatch:
    input_sha256: str
    raw_bytes: bytes
    raw_locator: str
    column_names: list[str]
    rows: list[dict[str, str]]


@dataclass
class SourceFieldModel:
    id: str
    source_record_id: str
    field_name: str
    field_value: str


@dataclass
class ProvenanceItem:
    source_record_id: str
    source_field_name: str
    source_field_value: str
    rule_matched: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_record_id": self.source_record_id,
            "source_field_name": self.source_field_name,
            "source_field_value": self.source_field_value,
            "rule_matched": self.rule_matched,
        }


@dataclass
class NormalizedRecord:
    row_id: str
    record_type: str  # "finding" or "detection"
    data: dict[str, Any]
    provenance: dict[str, ProvenanceItem] = field(default_factory=dict)
    has_fabricated_value: bool = False
    validation_error_shape: str | None = None
    validation_error_reason: str | None = None

    def to_validation_payload(self) -> dict[str, Any]:
        payload = dict(self.data)
        payload["record_type"] = self.record_type
        payload["has_fabricated_value"] = self.has_fabricated_value
        payload["provenance"] = {k: v.to_dict() for k, v in self.provenance.items()}
        return payload


@dataclass
class ValidationVerdict:
    row_id: str
    accepted: bool
    violated_shape: str | None = None
    reason: str | None = None


@dataclass
class RunManifest:
    run_id: str
    ontology_version: str
    mapping_version: str
    query_version: str
    input_sha256: str
    as_of: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "ontology_version": self.ontology_version,
            "mapping_version": self.mapping_version,
            "query_version": self.query_version,
            "input_sha256": self.input_sha256,
            "as_of": self.as_of,
        }
