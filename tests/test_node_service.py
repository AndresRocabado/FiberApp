import os
import sys

os.environ["DB_PATH"] = "test_fiber.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from database.connection import get_connection
from database.schema import initialize_database
from src.services.link_service import LinkService
from src.services.node_service import NodeService


@pytest.fixture(autouse=True)
def reset_db():
    initialize_database(drop_existing=True)


@pytest.fixture
def service():
    return NodeService()


class TestCreateNode:
    def test_creates_node_with_correct_fields(self, service):
        node = service.create_node("Nodo Central", "Bogota", "Central", "Activo")
        assert node.id is not None
        assert node.name == "Nodo Central"
        assert node.city == "Bogota"
        assert node.node_type.value == "Central"
        assert node.status.value == "Activo"

    def test_strips_whitespace_from_name_and_city(self, service):
        node = service.create_node("  Nodo A  ", "  Medellin  ", "Acceso", "Activo")
        assert node.name == "Nodo A"
        assert node.city == "Medellin"

    def test_raises_on_duplicate_name(self, service):
        service.create_node("Nodo Unico", "Cali", "Terminal", "Activo")
        with pytest.raises(ValueError, match="Ya existe un nodo"):
            service.create_node("Nodo Unico", "Bogota", "Central", "Inactivo")

    def test_raises_on_empty_name(self, service):
        with pytest.raises(ValueError, match="obligatorios"):
            service.create_node("", "Bogota", "Central", "Activo")

    def test_raises_on_empty_city(self, service):
        with pytest.raises(ValueError, match="obligatorios"):
            service.create_node("Nodo X", "", "Central", "Activo")


class TestGetNode:
    def test_returns_node_by_id(self, service):
        created = service.create_node("Nodo B", "Pereira", "Acceso", "Activo")
        fetched = service.get_node(created.id)
        assert fetched.id == created.id
        assert fetched.name == "Nodo B"

    def test_raises_for_nonexistent_id(self, service):
        with pytest.raises(ValueError, match="no encontrado"):
            service.get_node(9999)


class TestGetAllNodes:
    def test_returns_empty_list_initially(self, service):
        assert service.get_all_nodes() == []

    def test_returns_all_created_nodes(self, service):
        service.create_node("Nodo 1", "Bogota", "Central",  "Activo")
        service.create_node("Nodo 2", "Cali",   "Terminal", "Inactivo")
        nodes = service.get_all_nodes()
        assert len(nodes) == 2


class TestUpdateNode:
    def test_updates_all_fields(self, service):
        node    = service.create_node("Original", "Bogota", "Central", "Activo")
        updated = service.update_node(node.id, "Actualizado", "Cali", "Acceso", "Inactivo")
        assert updated.name      == "Actualizado"
        assert updated.city      == "Cali"
        assert updated.node_type.value == "Acceso"
        assert updated.status.value    == "Inactivo"

    def test_raises_on_duplicate_name_for_other_node(self, service):
        service.create_node("Nodo Existente", "Bogota", "Central", "Activo")
        n2 = service.create_node("Nodo Dos", "Cali", "Acceso", "Activo")
        with pytest.raises(ValueError, match="Ya existe un nodo"):
            service.update_node(n2.id, "Nodo Existente", "Cali", "Acceso", "Activo")

    def test_can_keep_same_name_when_updating(self, service):
        node    = service.create_node("Mismo Nombre", "Bogota", "Central", "Activo")
        updated = service.update_node(node.id, "Mismo Nombre", "Medellin", "Central", "Inactivo")
        assert updated.city == "Medellin"


class TestDeleteNode:
    def test_deletes_existing_node(self, service):
        node = service.create_node("Para Borrar", "Bogota", "Terminal", "Activo")
        assert service.delete_node(node.id) is True
        with pytest.raises(ValueError):
            service.get_node(node.id)

    def test_raises_for_nonexistent_node(self, service):
        with pytest.raises(ValueError, match="no encontrado"):
            service.delete_node(9999)


class TestNameReuseAfterDelete:
    def test_can_create_node_with_name_of_deleted_node(self, service):
        old = service.create_node("Reusado", "Bogota", "Central", "Activo")
        service.delete_node(old.id)
        new = service.create_node("Reusado", "Cali", "Acceso", "Activo")
        assert new.id != old.id

    def test_can_rename_to_name_of_deleted_node(self, service):
        old  = service.create_node("Viejo", "Bogota", "Central", "Activo")
        node = service.create_node("Otro", "Cali", "Acceso", "Activo")
        service.delete_node(old.id)
        updated = service.update_node(node.id, "Viejo", "Cali", "Acceso", "Activo")
        assert updated.name == "Viejo"

    def test_restore_fails_when_name_is_taken(self, service):
        old = service.create_node("Ocupado", "Bogota", "Central", "Activo")
        service.delete_node(old.id)
        service.create_node("Ocupado", "Cali", "Acceso", "Activo")
        with pytest.raises(ValueError, match="Ya existe un nodo activo"):
            service.restore_node(old.id)


class TestLegacySchemaMigration:
    def _create_legacy_schema(self):
        with get_connection() as conn:
            conn.execute("DROP TABLE IF EXISTS fiber_links")
            conn.execute("DROP TABLE IF EXISTS nodes")
            conn.execute("""
                CREATE TABLE nodes (
                    id         INTEGER PRIMARY KEY AUTOINCREMENT,
                    name       TEXT    NOT NULL UNIQUE,
                    city       TEXT    NOT NULL,
                    node_type  TEXT    NOT NULL,
                    status     TEXT    NOT NULL DEFAULT 'Activo',
                    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
                    deleted_at TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE fiber_links (
                    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
                    origin_node_id      INTEGER NOT NULL,
                    destination_node_id INTEGER NOT NULL,
                    distance_km         REAL    NOT NULL,
                    capacity_gbps       REAL    NOT NULL,
                    status              TEXT    NOT NULL DEFAULT 'Activo',
                    name                TEXT,
                    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
                    deleted_at          TEXT,
                    FOREIGN KEY (origin_node_id)      REFERENCES nodes(id) ON DELETE RESTRICT,
                    FOREIGN KEY (destination_node_id) REFERENCES nodes(id) ON DELETE RESTRICT
                )
            """)
            conn.execute("INSERT INTO nodes (id, name, city, node_type) VALUES (1, 'A', 'Bogota', 'Central')")
            conn.execute("INSERT INTO nodes (id, name, city, node_type, deleted_at) "
                         "VALUES (2, 'B', 'Cali', 'Acceso', datetime('now'))")
            conn.execute("INSERT INTO nodes (id, name, city, node_type) VALUES (3, 'C', 'Cali', 'Acceso')")
            conn.execute("INSERT INTO fiber_links (origin_node_id, destination_node_id, distance_km, capacity_gbps) "
                         "VALUES (1, 3, 5.0, 10.0)")

    def test_migration_keeps_data_and_allows_reusing_deleted_names(self, service):
        self._create_legacy_schema()
        initialize_database()

        assert [n.name for n in service.get_all_nodes()] == ["A", "C"]
        assert [n.id for n in service.get_deleted_nodes()] == [2]
        assert len(LinkService().get_all_links()) == 1

        reused = service.create_node("B", "Cali", "Acceso", "Activo")
        assert reused.id == 4

    def test_migration_keeps_foreign_keys_enforced(self):
        self._create_legacy_schema()
        initialize_database()
        with get_connection() as conn:
            assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
            with pytest.raises(Exception, match="FOREIGN KEY"):
                conn.execute("DELETE FROM nodes WHERE id = 1")

    def test_active_names_stay_unique_at_db_level(self):
        initialize_database()
        with get_connection() as conn:
            conn.execute("INSERT INTO nodes (name, city, node_type) VALUES ('X', 'Bogota', 'Central')")
            with pytest.raises(Exception, match="UNIQUE"):
                conn.execute("INSERT INTO nodes (name, city, node_type) VALUES ('X', 'Cali', 'Acceso')")
