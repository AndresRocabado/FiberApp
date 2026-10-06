import os
import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Generator, Optional

_active_conn: ContextVar[Optional[sqlite3.Connection]] = ContextVar("_active_conn", default=None)


def _open_connection() -> sqlite3.Connection:
    db_path = os.getenv("DB_PATH", "fiber_network.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    # Inside transaction(), reuse its connection and leave commit/rollback to it.
    active = _active_conn.get()
    if active is not None:
        yield active
        return
    conn = _open_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def transaction() -> Generator[sqlite3.Connection, None, None]:
    """Runs every get_connection() inside the block on one connection, committed or rolled back as a unit."""
    if _active_conn.get() is not None:
        with get_connection() as conn:
            yield conn
        return
    with get_connection() as conn:
        token = _active_conn.set(conn)
        try:
            yield conn
        finally:
            _active_conn.reset(token)
