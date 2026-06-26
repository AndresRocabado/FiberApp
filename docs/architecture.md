# Architecture - Fiber Network Management System

## Layer Diagram

```
+----------------------------+
|   UI Layer (Streamlit)     |  app.py
+----------------------------+
            |
+----------------------------+
|   Service Layer            |  src/services/
|  - NodeService             |
|  - LinkService             |
|  - ReportService           |
+----------------------------+
            |
+----------------------------+
|   Repository Layer         |  src/repositories/
|  - NodeRepository          |
|  - LinkRepository          |
+----------------------------+
            |
+----------------------------+
|   Database Layer           |  database/
|  - connection.py           |
|  - schema.py               |
+----------------------------+
            |
+----------------------------+
|   SQLite / PostgreSQL      |
+----------------------------+
```

## Design Decisions

### Repository Pattern
Each entity has a dedicated repository that encapsulates all SQL queries.
Services never write SQL directly.

### Service Layer
Business rules (validation, constraints) live exclusively in services.
Repositories only handle persistence.

### Models as Dataclasses
`Node` and `FiberLink` are plain dataclasses with `from_row()` factory methods
that convert `sqlite3.Row` results into typed objects.

### Context Manager for Connections
`get_connection()` is a context manager that handles commit/rollback automatically,
ensuring no connection is left open.

## Database Schema

```
nodes
-----
id          INTEGER PK
name        TEXT UNIQUE NOT NULL
city        TEXT NOT NULL
node_type   TEXT NOT NULL  -- Central | Distribucion | Acceso | Terminal
status      TEXT NOT NULL  -- Activo | Inactivo | Mantenimiento
created_at  TEXT NOT NULL

fiber_links
-----------
id                  INTEGER PK
origin_node_id      INTEGER FK -> nodes.id
destination_node_id INTEGER FK -> nodes.id
distance_km         REAL > 0
capacity_gbps       REAL > 0
status              TEXT   -- Activo | Inactivo | Mantenimiento
created_at          TEXT
```
