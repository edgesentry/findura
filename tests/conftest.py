from pathlib import Path

import psycopg
import pytest

from harness.db import get_connection, init_db, truncate_all_tables


@pytest.fixture(scope="session")
def db_conn():
    conn = get_connection()
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clean_db(db_conn):
    try:
        db_conn.rollback()
    except psycopg.Error:
        pass
    truncate_all_tables(db_conn)
    yield
    try:
        db_conn.rollback()
    except psycopg.Error:
        pass
    truncate_all_tables(db_conn)


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent
