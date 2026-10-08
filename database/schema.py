import sqlite3
from typing import Callable, List, Tuple

from database.connection import get_connection

_CREATE_SCHEMA_VERSION = """
CREATE TABLE IF NOT EXISTS schema_version (
    version    INTEGER PRIMARY KEY,
    applied_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

_CREATE_NODES = """
CREATE TABLE IF NOT EXISTS nodes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    city       TEXT    NOT NULL,
    node_type  TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'Activo',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""

_CREATE_LINKS = """
CREATE TABLE IF NOT EXISTS fiber_links (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_node_id      INTEGER NOT NULL,
    destination_node_id INTEGER NOT NULL,
    distance_km         REAL    NOT NULL,
    capacity_gbps       REAL    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'Activo',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (origin_node_id)      REFERENCES nodes(id) ON DELETE RESTRICT,
    FOREIGN KEY (destination_node_id) REFERENCES nodes(id) ON DELETE RESTRICT,
    CHECK (origin_node_id != destination_node_id),
    CHECK (distance_km   > 0),
    CHECK (capacity_gbps > 0)
);
"""

# Links trashed before deleted_by_node_id existed: treat them as cascade-deleted when
# their deleted_at matches (within a second) the deleted_at of one of their nodes.
_BACKFILL_DELETED_BY_NODE = """
UPDATE fiber_links
SET deleted_by_node_id = (
    SELECT n.id FROM nodes n
    WHERE  n.id IN (fiber_links.origin_node_id, fiber_links.destination_node_id)
      AND  n.deleted_at IS NOT NULL
      AND  ABS(strftime('%s', n.deleted_at) - strftime('%s', fiber_links.deleted_at)) <= 1
    LIMIT 1
)
WHERE deleted_at IS NOT NULL
"""


def _has_column(conn: sqlite3.Connection, table: str, column: str) -> bool:
    return any(row["name"] == column for row in conn.execute(f"PRAGMA table_info({table})"))


def _add_column(conn: sqlite3.Connection, table: str, column: str, definition: str) -> bool:
    """Adds the column unless it's already there; returns whether it was added."""
    if _has_column(conn, table, column):
        return False
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
    return True


# Databases created before schema_version existed start at version 0 with some of
# these changes already in place, so every migration checks the actual schema
# instead of assuming it. Once applied, a version is never run again.

def _m001_initial_tables(conn: sqlite3.Connection) -> None:
    conn.execute(_CREATE_NODES)
    conn.execute(_CREATE_LINKS)


def _m002_link_name(conn: sqlite3.Connection) -> None:
    _add_column(conn, "fiber_links", "name", "TEXT")


def _m003_soft_delete(conn: sqlite3.Connection) -> None:
    _add_column(conn, "nodes", "deleted_at", "TEXT")
    _add_column(conn, "fiber_links", "deleted_at", "TEXT")


def _m004_deleted_by_node(conn: sqlite3.Connection) -> None:
    # Set when a link is trashed together with one of its nodes, so restoring
    # the node brings back only those links and not ones deleted by hand.
    if _add_column(conn, "fiber_links", "deleted_by_node_id", "INTEGER"):
        conn.execute(_BACKFILL_DELETED_BY_NODE)


def _m005_unique_active_node_names(conn: sqlite3.Connection) -> None:
    # Names only need to be unique among active nodes, so a node in the trash
    # doesn't block reusing its name. Older databases declared `name UNIQUE` on the
    # column itself; SQLite can't drop that constraint, so the table is rebuilt.
    sql = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'nodes'"
    ).fetchone()["sql"]
    if "UNIQUE" in sql.upper():
        conn.execute("""
            CREATE TABLE nodes_new (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                name       TEXT    NOT NULL,
                city       TEXT    NOT NULL,
                node_type  TEXT    NOT NULL,
                status     TEXT    NOT NULL DEFAULT 'Activo',
                created_at TEXT    NOT NULL DEFAULT (datetime('now')),
                deleted_at TEXT
            )
        """)
        conn.execute("""
            INSERT INTO nodes_new (id, name, city, node_type, status, created_at, deleted_at)
                SELECT id, name, city, node_type, status, created_at, deleted_at FROM nodes
        """)
        conn.execute("DROP TABLE nodes")
        conn.execute("ALTER TABLE nodes_new RENAME TO nodes")
    conn.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_nodes_name_active ON nodes(name) WHERE deleted_at IS NULL"
    )


def _m006_indexes(conn: sqlite3.Connection) -> None:
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_deleted_at ON nodes(deleted_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_city       ON nodes(city)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_status     ON nodes(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_node_type  ON nodes(node_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_links_deleted_at ON fiber_links(deleted_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_links_status     ON fiber_links(status)")


# Append new migrations at the end; never renumber or edit one already released.
MIGRATIONS: List[Tuple[int, Callable[[sqlite3.Connection], None]]] = [
    (1, _m001_initial_tables),
    (2, _m002_link_name),
    (3, _m003_soft_delete),
    (4, _m004_deleted_by_node),
    (5, _m005_unique_active_node_names),
    (6, _m006_indexes),
]


def get_schema_version(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()[0]


def _apply_migration(conn: sqlite3.Connection, version: int, migrate) -> None:
    # Foreign keys are off so tables can be rebuilt (the pragma is a no-op inside a
    # transaction); foreign_key_check below makes sure nothing was left dangling.
    conn.commit()
    conn.execute("PRAGMA foreign_keys = OFF")
    try:
        conn.execute("BEGIN")
        try:
            migrate(conn)
            if conn.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise RuntimeError(f"Migration {version} left foreign key violations")
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
            conn.commit()
        except Exception:
            conn.rollback()
            raise
    finally:
        conn.execute("PRAGMA foreign_keys = ON")


def initialize_database(drop_existing: bool = False) -> None:
    with get_connection() as conn:
        if drop_existing:
            conn.execute("DROP TABLE IF EXISTS fiber_links")
            conn.execute("DROP TABLE IF EXISTS nodes")
            conn.execute("DROP TABLE IF EXISTS schema_version")
        conn.execute(_CREATE_SCHEMA_VERSION)

        current = get_schema_version(conn)
        for version, migrate in MIGRATIONS:
            if version > current:
                _apply_migration(conn, version, migrate)
