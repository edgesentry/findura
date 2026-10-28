import csv
import hashlib
import io
import json
from pathlib import Path

from harness.models import RawBatch


def ingest_file(file_path: str | Path, conn) -> RawBatch:
    path = Path(file_path)
    with open(path, "rb") as f:
        raw_bytes = f.read()

    input_sha256 = hashlib.sha256(raw_bytes).hexdigest()
    text = raw_bytes.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    fieldnames = list(reader.fieldnames or [])
    rows = [row for row in reader]

    raw_batch = RawBatch(
        input_sha256=input_sha256,
        raw_bytes=raw_bytes,
        raw_locator=str(path.resolve()),
        column_names=fieldnames,
        rows=rows,
    )

    with conn.cursor() as cur:
        # Check if already ingested
        cur.execute(
            "SELECT input_sha256 FROM raw_batches WHERE input_sha256 = %s",
            (input_sha256,),
        )
        if cur.fetchone():
            return raw_batch

        # Save raw batch
        cur.execute(
            """
            INSERT INTO raw_batches (input_sha256, raw_bytes, raw_locator, column_names)
            VALUES (%s, %s, %s, %s)
            """,
            (
                input_sha256,
                raw_bytes,
                raw_batch.raw_locator,
                json.dumps(fieldnames),
            ),
        )

        # Save source records and fields
        for idx, row in enumerate(rows):
            rec_id = f"{input_sha256[:16]}-row-{idx + 1:04d}"
            cur.execute(
                """
                INSERT INTO source_records (id, input_sha256, row_index, raw_locator)
                VALUES (%s, %s, %s, %s)
                """,
                (rec_id, input_sha256, idx + 1, f"{path}:{idx + 2}"),
            )
            for col_name, val in row.items():
                if col_name is None:
                    continue
                field_id = f"{rec_id}-{col_name}"
                cur.execute(
                    """
                    INSERT INTO source_fields (id, source_record_id, field_name, field_value)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (field_id, rec_id, col_name, val),
                )

    conn.commit()
    return raw_batch
