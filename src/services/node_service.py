from typing import List, Optional

from src.models.node import Node, NodeType, OperationalStatus
from src.repositories.node_repository import NodeRepository


class NodeService:
    def __init__(self, repository: Optional[NodeRepository] = None) -> None:
        self._repo = repository or NodeRepository()

    def create_node(self, name: str, city: str, node_type: str, status: str) -> Node:
        name = name.strip()
        city = city.strip()
        if not name or not city:
            raise ValueError("El nombre y la ciudad son obligatorios")
        if self._repo.exists_by_name(name):
            raise ValueError(f"Ya existe un nodo con el nombre '{name}'")
        node = Node(
            name=name,
            city=city,
            node_type=NodeType(node_type),
            status=OperationalStatus(status),
        )
        return self._repo.create(node)

    def get_node(self, node_id: int) -> Node:
        node = self._repo.get_by_id(node_id)
        if node is None:
            raise ValueError(f"Nodo con ID {node_id} no encontrado")
        return node

    def get_all_nodes(self) -> List[Node]:
        return self._repo.get_all()

    def get_nodes_by_city(self, city: str) -> List[Node]:
        return self._repo.get_by_city(city)

    def update_node(self, node_id: int, name: str, city: str, node_type: str, status: str) -> Node:
        name = name.strip()
        city = city.strip()
        if not name or not city:
            raise ValueError("El nombre y la ciudad son obligatorios")
        node = self.get_node(node_id)
        if self._repo.exists_by_name(name, exclude_id=node_id):
            raise ValueError(f"Ya existe un nodo con el nombre '{name}'")
        node.name      = name
        node.city      = city
        node.node_type = NodeType(node_type)
        node.status    = OperationalStatus(status)
        return self._repo.update(node)

    def delete_node(self, node_id: int) -> bool:
        self.get_node(node_id)
        if not self._repo.delete(node_id):
            raise RuntimeError(f"No se pudo eliminar el nodo con ID {node_id}")
        return True
