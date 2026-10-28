import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from harness.resources import get_tables_sql_path


def get_connection_string() -> str:
    if "DATABASE_URL" in os.environ:
        return os.environ["DATABASE_URL"]

    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    user = os.environ.get("POSTGRES_USER", "findura")
    password = os.environ.get("POSTGRES_PASSWORD", "findura_password")
    dbname = os.environ.get("POSTGRES_DB", "findura")

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def get_connection():
    return psycopg.connect(get_connection_string(), row_factory=dict_row)


def init_db(conn, schema_path: Path | str | None = None):
    if schema_path is None:
        schema_path = get_tables_sql_path()
    else:
        schema_path = Path(schema_path)

    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()


def truncate_all_tables(conn):
    tables = [
        "value_provenance",
        "quarantine_records",
        "deadlines",
        "remediations",
        "findings",
        "detections",
        "inspections",
        "assets",
        "buildings",
        "source_fields",
        "source_records",
        "raw_batches",
    ]
    with conn.cursor() as cur:
        cur.execute(f"TRUNCATE TABLE {', '.join(tables)} RESTART IDENTITY CASCADE;")
    conn.commit()
