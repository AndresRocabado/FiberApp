import os
import sys

os.environ["DB_PATH"] = "test_fiber.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from database.schema import initialize_database
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
