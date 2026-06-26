import os
import sqlite3
from contextlib import contextmanager
from typing import Generator


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    db_path = os.getenv("DB_PATH", "fiber_network.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
