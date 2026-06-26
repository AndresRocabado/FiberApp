from database.connection import get_connection

_CREATE_NODES = """
CREATE TABLE IF NOT EXISTS nodes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE,
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


def initialize_database(drop_existing: bool = False) -> None:
    with get_connection() as conn:
        if drop_existing:
            conn.execute("DROP TABLE IF EXISTS fiber_links")
            conn.execute("DROP TABLE IF EXISTS nodes")
        conn.execute(_CREATE_NODES)
        conn.execute(_CREATE_LINKS)
