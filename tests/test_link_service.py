import os
import sys

os.environ["DB_PATH"] = "test_fiber.db"
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from database.schema import initialize_database
from src.services.link_service import LinkService
from src.services.node_service import NodeService


@pytest.fixture(autouse=True)
def reset_db():
    initialize_database(drop_existing=True)


@pytest.fixture
def node_service():
    return NodeService()


@pytest.fixture
def link_service():
    return LinkService()


@pytest.fixture
def two_nodes(node_service):
    n1 = node_service.create_node("Nodo A", "Bogota",   "Central", "Activo")
    n2 = node_service.create_node("Nodo B", "Medellin", "Acceso",  "Activo")
    return n1, n2


class TestCreateLink:
    def test_creates_link_between_two_nodes(self, link_service, two_nodes):
        n1, n2 = two_nodes
        lnk = link_service.create_link(n1.id, n2.id, 100.5, 10.0, "Activo")
        assert lnk.id is not None
        assert lnk.origin_node_id      == n1.id
        assert lnk.destination_node_id == n2.id
        assert lnk.distance_km         == 100.5
        assert lnk.capacity_gbps       == 10.0
        assert lnk.status.value        == "Activo"

    def test_raises_when_origin_equals_destination(self, link_service, two_nodes):
        n1, _ = two_nodes
        with pytest.raises(ValueError, match="mismo"):
            link_service.create_link(n1.id, n1.id, 10.0, 5.0, "Activo")

    def test_raises_on_nonexistent_origin_node(self, link_service, two_nodes):
        _, n2 = two_nodes
        with pytest.raises(ValueError, match="origen"):
            link_service.create_link(9999, n2.id, 10.0, 5.0, "Activo")

    def test_raises_on_nonexistent_destination_node(self, link_service, two_nodes):
        n1, _ = two_nodes
        with pytest.raises(ValueError, match="destino"):
            link_service.create_link(n1.id, 9999, 10.0, 5.0, "Activo")

    def test_raises_on_zero_distance(self, link_service, two_nodes):
        n1, n2 = two_nodes
        with pytest.raises(ValueError, match="distancia"):
            link_service.create_link(n1.id, n2.id, 0, 5.0, "Activo")

    def test_raises_on_zero_capacity(self, link_service, two_nodes):
        n1, n2 = two_nodes
        with pytest.raises(ValueError, match="capacidad"):
            link_service.create_link(n1.id, n2.id, 10.0, 0, "Activo")


class TestGetLink:
    def test_returns_link_with_node_names(self, link_service, two_nodes):
        n1, n2 = two_nodes
        created = link_service.create_link(n1.id, n2.id, 50.0, 20.0, "Activo")
        fetched = link_service.get_link(created.id)
        assert fetched.origin_node_name      == "Nodo A"
        assert fetched.destination_node_name == "Nodo B"

    def test_raises_for_nonexistent_id(self, link_service):
        with pytest.raises(ValueError, match="no encontrado"):
            link_service.get_link(9999)


class TestGetAllLinks:
    def test_returns_empty_list_initially(self, link_service):
        assert link_service.get_all_links() == []

    def test_returns_all_created_links(self, link_service, two_nodes):
        n1, n2 = two_nodes
        link_service.create_link(n1.id, n2.id, 10.0, 5.0,  "Activo")
        link_service.create_link(n2.id, n1.id, 20.0, 10.0, "Inactivo")
        assert len(link_service.get_all_links()) == 2


class TestUpdateLink:
    def test_updates_distance_and_status(self, link_service, two_nodes):
        n1, n2  = two_nodes
        lnk     = link_service.create_link(n1.id, n2.id, 10.0, 5.0, "Activo")
        updated = link_service.update_link(lnk.id, n1.id, n2.id, 999.9, 100.0, "Inactivo")
        assert updated.distance_km   == 999.9
        assert updated.capacity_gbps == 100.0
        assert updated.status.value  == "Inactivo"


class TestDeleteLink:
    def test_deletes_existing_link(self, link_service, two_nodes):
        n1, n2 = two_nodes
        lnk    = link_service.create_link(n1.id, n2.id, 10.0, 5.0, "Activo")
        assert link_service.delete_link(lnk.id) is True
        with pytest.raises(ValueError):
            link_service.get_link(lnk.id)

    def test_raises_for_nonexistent_link(self, link_service):
        with pytest.raises(ValueError, match="no encontrado"):
            link_service.delete_link(9999)
