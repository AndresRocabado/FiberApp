-- Fiber Network Management System - Initial Schema
-- Compatible with SQLite (default) and adaptable to PostgreSQL

CREATE TABLE IF NOT EXISTS nodes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL UNIQUE,
    city       TEXT    NOT NULL,
    node_type  TEXT    NOT NULL CHECK(node_type IN ('Central', 'Distribución', 'Acceso', 'Terminal')),
    status     TEXT    NOT NULL DEFAULT 'Activo' CHECK(status IN ('Activo', 'Inactivo', 'Mantenimiento')),
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS fiber_links (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    origin_node_id      INTEGER NOT NULL,
    destination_node_id INTEGER NOT NULL,
    distance_km         REAL    NOT NULL CHECK(distance_km   > 0),
    capacity_gbps       REAL    NOT NULL CHECK(capacity_gbps > 0),
    status              TEXT    NOT NULL DEFAULT 'Activo' CHECK(status IN ('Activo', 'Inactivo', 'Mantenimiento')),
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (origin_node_id)      REFERENCES nodes(id) ON DELETE RESTRICT,
    FOREIGN KEY (destination_node_id) REFERENCES nodes(id) ON DELETE RESTRICT,
    CHECK (origin_node_id != destination_node_id)
);
