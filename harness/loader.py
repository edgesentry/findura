import json
from pathlib import Path
from typing import Any

import jsonschema

from harness.models import NormalizedRecord, ValidationVerdict


class ConstraintValidator:
    def __init__(self, schema_dir: Path | str | None = None):
        if schema_dir is None:
            schema_dir = Path(__file__).resolve().parent.parent / "schema"
        else:
            schema_dir = Path(schema_dir)

        self.schema_dir = schema_dir
        self.schemas: dict[str, dict[str, Any]] = {}

        shape_files = {
            "FindingHasDeadlineShape": "finding_has_deadline.schema.json",
            "CompletedRemediationHasDateShape": "completed_remediation_has_date.schema.json",
            "DateImpliesCompletedShape": "date_implies_completed.schema.json",
            "InspectionHasOneAssetShape": "inspection_has_one_asset.schema.json",
            "NoFabricatedValueShape": "no_fabricated_value.schema.json",
        }

        for shape_name, filename in shape_files.items():
            path = schema_dir / filename
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    self.schemas[shape_name] = json.load(f)

    def validate_record(self, record: NormalizedRecord) -> ValidationVerdict:
        if record.validation_error_shape:
            return ValidationVerdict(
                row_id=record.row_id,
                accepted=False,
                violated_shape=record.validation_error_shape,
                reason=record.validation_error_reason or "Normalization validation error",
            )

        payload = record.to_validation_payload()

        for shape_name, schema in self.schemas.items():
            try:
                jsonschema.validate(
                    instance=payload,
                    schema=schema,
                )
            except jsonschema.ValidationError as e:
                return ValidationVerdict(
                    row_id=record.row_id,
                    accepted=False,
                    violated_shape=shape_name,
                    reason=f"{shape_name} violation: {e.message}",
                )

        return ValidationVerdict(row_id=record.row_id, accepted=True)


def load_records(
    records: list[NormalizedRecord],
    conn,
    input_sha256: str,
    ontology_version: str = "1",
    mapping_version: str = "1",
    run_id: str = "00000000-0000-0000-0000-000000000001",
    schema_dir: Path | str | None = None,
) -> list[ValidationVerdict]:
    validator = ConstraintValidator(schema_dir)
    verdicts: list[ValidationVerdict] = []

    with conn.cursor() as cur:
        for rec in records:
            verdict = validator.validate_record(rec)
            verdicts.append(verdict)

            if not verdict.accepted:
                # Save to quarantine_records
                cur.execute(
                    """
                    INSERT INTO quarantine_records (
                        input_sha256, ontology_version, mapping_version,
                        violated_shape, reason, rejected_record, run_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    (
                        input_sha256,
                        ontology_version,
                        mapping_version,
                        verdict.violated_shape,
                        verdict.reason,
                        json.dumps(rec.to_validation_payload()),
                        run_id,
                    ),
                )
            else:
                # Store in core tables
                data = rec.data

                # Building
                b_key = data.get("building", {}).get("building_key")
                building_id = None
                if b_key:
                    cur.execute(
                        "INSERT INTO buildings (building_key) VALUES (%s) ON CONFLICT (building_key) DO UPDATE SET building_key = EXCLUDED.building_key RETURNING id",
                        (b_key,),
                    )
                    building_id = cur.fetchone()["id"]

                # Asset
                a_key = data.get("asset", {}).get("asset_key")
                asset_id = None
                if a_key and building_id:
                    cur.execute(
                        "INSERT INTO assets (asset_key, building_id) VALUES (%s, %s) ON CONFLICT (asset_key) DO UPDATE SET building_id = EXCLUDED.building_id RETURNING id",
                        (a_key, building_id),
                    )
                    asset_id = cur.fetchone()["id"]

                if rec.record_type == "finding":
                    # Inspection
                    insp_data = data.get("inspection", {})
                    insp_key = insp_data.get("inspection_key")
                    cur.execute(
                        """
                        INSERT INTO inspections (inspection_key, asset_id, conducted_on, inspection_kind, conducted_by)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (inspection_key) DO UPDATE SET
                            conducted_on = EXCLUDED.conducted_on,
                            inspection_kind = EXCLUDED.inspection_kind,
                            conducted_by = EXCLUDED.conducted_by
                        RETURNING id
                        """,
                        (
                            insp_key,
                            asset_id,
                            insp_data.get("conducted_on"),
                            insp_data.get("inspection_kind"),
                            insp_data.get("conducted_by"),
                        ),
                    )
                    inspection_id = cur.fetchone()["id"]

                    # Finding
                    f_data = data.get("finding", {})
                    f_key = f_data.get("finding_key")
                    cur.execute(
                        """
                        INSERT INTO findings (finding_key, inspection_id, statement, found_on)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (finding_key) DO UPDATE SET
                            statement = EXCLUDED.statement,
                            found_on = EXCLUDED.found_on
                        RETURNING id
                        """,
                        (
                            f_key,
                            inspection_id,
                            f_data.get("statement"),
                            f_data.get("found_on"),
                        ),
                    )
                    finding_id = cur.fetchone()["id"]

                    # Deadlines (exactly 1)
                    deadlines = f_data.get("deadlines", [])
                    if deadlines:
                        due_on = deadlines[0].get("due_on")
                        cur.execute(
                            """
                            INSERT INTO deadlines (finding_id, due_on)
                            VALUES (%s, %s)
                            ON CONFLICT (finding_id) DO UPDATE SET due_on = EXCLUDED.due_on
                            RETURNING id
                            """,
                            (finding_id, due_on),
                        )

                    # Remediation
                    rem_data = data.get("remediation", {})
                    completed = rem_data.get("completed", False)
                    completed_on = rem_data.get("completed_on")
                    cur.execute(
                        """
                        INSERT INTO remediations (finding_id, completed, completed_on)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (finding_id) DO UPDATE SET
                            completed = EXCLUDED.completed,
                            completed_on = EXCLUDED.completed_on
                        RETURNING id
                        """,
                        (finding_id, completed, completed_on),
                    )

                    # Value provenance
                    for target_prop, prov in rec.provenance.items():
                        core_table = "findings"
                        core_id = f_key
                        if "conductedOn" in target_prop or "inspection" in target_prop:
                            core_table = "inspections"
                            core_id = insp_key
                        elif "dueOn" in target_prop:
                            core_table = "deadlines"
                            core_id = f_key
                        elif "completed" in target_prop:
                            core_table = "remediations"
                            core_id = f_key

                        source_field_id = f"{prov.source_record_id}-{prov.source_field_name}"
                        cur.execute(
                            """
                            INSERT INTO value_provenance (
                                core_table, core_id, property_name,
                                source_record_id, source_field_id,
                                source_field_name, source_field_value
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            (
                                core_table,
                                core_id,
                                target_prop,
                                prov.source_record_id,
                                source_field_id,
                                prov.source_field_name,
                                prov.source_field_value,
                            ),
                        )

                elif rec.record_type == "detection":
                    det_data = data.get("detection", {})
                    det_key = det_data.get("detection_key")
                    cur.execute(
                        """
                        INSERT INTO detections (detection_key, asset_id, detected_on)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (detection_key) DO UPDATE SET
                            detected_on = EXCLUDED.detected_on
                        RETURNING id
                        """,
                        (det_key, asset_id, det_data.get("detected_on")),
                    )

    conn.commit()
    return verdicts
