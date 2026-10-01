from database.connection import get_connection

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
    name                TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (origin_node_id)      REFERENCES nodes(id) ON DELETE RESTRICT,
    FOREIGN KEY (destination_node_id) REFERENCES nodes(id) ON DELETE RESTRICT,
    CHECK (origin_node_id != destination_node_id),
    CHECK (distance_km   > 0),
    CHECK (capacity_gbps > 0)
);
"""

# Names only need to be unique among active nodes, so a node in the trash
# doesn't block reusing its name. Older databases declared `name UNIQUE` on the
# column itself; SQLite can't drop that constraint, so the table is rebuilt.
_REBUILD_NODES_WITHOUT_UNIQUE = """
PRAGMA foreign_keys = OFF;
BEGIN;
CREATE TABLE nodes_new (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    city       TEXT    NOT NULL,
    node_type  TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT 'Activo',
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    deleted_at TEXT
);
INSERT INTO nodes_new (id, name, city, node_type, status, created_at, deleted_at)
    SELECT id, name, city, node_type, status, created_at, deleted_at FROM nodes;
DROP TABLE nodes;
ALTER TABLE nodes_new RENAME TO nodes;
COMMIT;
PRAGMA foreign_keys = ON;
"""


def _nodes_has_unique_name(conn) -> bool:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'nodes'"
    ).fetchone()
    return row is not None and "UNIQUE" in row["sql"].upper()


def initialize_database(drop_existing: bool = False) -> None:
    with get_connection() as conn:
        if drop_existing:
            conn.execute("DROP TABLE IF EXISTS fiber_links")
            conn.execute("DROP TABLE IF EXISTS nodes")
        conn.execute(_CREATE_NODES)
        conn.execute(_CREATE_LINKS)
        try:
            conn.execute("ALTER TABLE fiber_links ADD COLUMN name TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE nodes ADD COLUMN deleted_at TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE fiber_links ADD COLUMN deleted_at TEXT")
        except Exception:
            pass

        if _nodes_has_unique_name(conn):
            conn.executescript(_REBUILD_NODES_WITHOUT_UNIQUE)

        conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_nodes_name_active ON nodes(name) WHERE deleted_at IS NULL"
        )
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_deleted_at ON nodes(deleted_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_city       ON nodes(city)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_status     ON nodes(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_nodes_node_type  ON nodes(node_type)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_links_deleted_at ON fiber_links(deleted_at)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_links_status     ON fiber_links(status)")
