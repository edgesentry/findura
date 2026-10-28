from datetime import datetime
from pathlib import Path
from typing import Any

import yaml

from harness.models import NormalizedRecord, ProvenanceItem, RawBatch


def load_mapping(mapping_path: str | Path) -> dict[str, Any]:
    with open(mapping_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_batch(
    raw_batch: RawBatch, mapping: dict[str, Any]
) -> list[NormalizedRecord]:
    rules = mapping.get("rules", [])
    records: list[NormalizedRecord] = []

    for idx, row in enumerate(raw_batch.rows):
        rec_id = f"{raw_batch.input_sha256[:16]}-row-{idx + 1:04d}"
        row_id = row.get("row_id") or f"row-{idx + 1:02d}"
        record_type = row.get("record_type", "finding")

        prov_map: dict[str, ProvenanceItem] = {}
        has_fabricated = False
        error_shape: str | None = None
        error_reason: str | None = None

        mapped_values: dict[str, Any] = {}

        for rule in rules:
            src_col = rule["source"]
            target = rule["target"]
            transform = rule.get("transform", "rename")
            on_missing = rule.get("on_missing", "omit")

            if src_col not in row or row[src_col] is None or row[src_col] == "":
                if on_missing == "omit":
                    continue
                else:
                    mapped_values[target] = None
                    continue

            val = row[src_col]
            prov_item = ProvenanceItem(
                source_record_id=rec_id,
                source_field_name=src_col,
                source_field_value=val,
                rule_matched=True,
            )

            # Apply transform
            if transform == "rename":
                mapped_values[target] = val
                prov_map[target] = prov_item

            elif isinstance(transform, dict) and transform.get("op") == "parse_date":
                pattern = transform.get("pattern", "%Y-%m-%d")
                try:
                    dt = datetime.strptime(val, pattern)
                    iso_date = dt.strftime("%Y-%m-%d")
                    mapped_values[target] = iso_date
                    prov_map[target] = prov_item
                except (ValueError, TypeError) as e:
                    # Parse error
                    if target == "insp:dueOn":
                        error_shape = "FindingHasDeadlineShape"
                        error_reason = f"Invalid due_date format: {val}"
                    else:
                        has_fabricated = True
                        error_shape = "NoFabricatedValueShape"
                        error_reason = (
                            f"Transformation failed for {src_col}: {val} ({e})"
                        )
                    mapped_values[target] = val
                    prov_map[target] = prov_item

            elif isinstance(transform, dict) and transform.get("op") == "enum_map":
                values_map = transform.get("values", {})
                if val in values_map:
                    mapped_values[target] = values_map[val]
                    prov_map[target] = prov_item
                else:
                    # Unapproved enum value
                    has_fabricated = True
                    error_shape = "NoFabricatedValueShape"
                    error_reason = f"Unapproved enum value for {src_col}: {val}"
                    mapped_values[target] = val
                    prov_map[target] = prov_item

            elif isinstance(transform, dict) and transform.get("op") == "split":
                sep = transform.get("separator", "|")
                parts = val.split(sep)
                targets = target if isinstance(target, list) else [target]
                if len(parts) == len(targets):
                    for t, p in zip(targets, parts):
                        p_stripped = p.strip()
                        mapped_values[t] = p_stripped if p_stripped else None
                        prov_map[t] = prov_item
                else:
                    has_fabricated = True
                    error_shape = "InspectionHasOneAssetShape"
                    error_reason = f"Split target count mismatch for {src_col}: {val}"

        # Construct structured payload according to core ontology
        data: dict[str, Any] = {}
        building_key = mapped_values.get("insp:buildingKey")
        asset_key = mapped_values.get("insp:assetKey")

        if building_key:
            data["building"] = {"building_key": building_key}
        if asset_key:
            data["asset"] = {"asset_key": asset_key}

        if record_type == "finding":
            inspection_key = mapped_values.get("insp:inspectionKey")
            conducted_on = mapped_values.get("insp:conductedOn")
            inspection_kind = mapped_values.get("insp:inspectionKind")
            conducted_by = mapped_values.get("insp:conductedBy")

            inspected_assets = [asset_key] if asset_key else []
            data["inspection"] = {
                "inspection_key": inspection_key,
                "conducted_on": conducted_on,
                "inspection_kind": inspection_kind,
                "conducted_by": conducted_by,
                "inspected_assets": inspected_assets,
            }

            finding_key = mapped_values.get("insp:findingKey")
            statement = mapped_values.get("insp:statement")
            found_on = mapped_values.get("insp:foundOn")
            due_on = mapped_values.get("insp:dueOn")

            # Check if due_date was raw invalid date string (e.g. not-a-date)
            raw_due = row.get("due_date", "")
            if not due_on and raw_due:
                # Raw was present but parse failed or invalid
                error_shape = error_shape or "FindingHasDeadlineShape"
                error_reason = error_reason or "Invalid due_date format"

            deadlines = []
            if due_on:
                deadlines.append({"due_on": due_on})

            data["finding"] = {
                "finding_key": finding_key,
                "statement": statement,
                "found_on": found_on,
                "deadlines": deadlines,
            }

            completed = mapped_values.get("insp:completed")
            completed_on = mapped_values.get("insp:completedOn")

            data["remediation"] = {
                "completed": completed if completed is not None else False,
                "completed_on": completed_on,
            }

        elif record_type == "detection":
            detection_key = mapped_values.get("insp:detectionKey")
            detected_on = mapped_values.get("insp:detectedOn")
            data["detection"] = {
                "detection_key": detection_key,
                "detected_on": detected_on,
                "asset_key": asset_key,
            }

        rec = NormalizedRecord(
            row_id=row_id,
            record_type=record_type,
            data=data,
            provenance=prov_map,
            has_fabricated_value=has_fabricated,
            validation_error_shape=error_shape,
            validation_error_reason=error_reason,
        )
        records.append(rec)

    return records
