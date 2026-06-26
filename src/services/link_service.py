from typing import List, Optional

from src.models.link import FiberLink, LinkStatus
from src.repositories.link_repository import LinkRepository
from src.repositories.node_repository import NodeRepository


class LinkService:
    def __init__(
        self,
        link_repo: Optional[LinkRepository] = None,
        node_repo: Optional[NodeRepository] = None,
    ) -> None:
        self._links = link_repo or LinkRepository()
        self._nodes = node_repo or NodeRepository()

    def _validate_nodes(self, origin_id: int, destination_id: int) -> None:
        if origin_id == destination_id:
            raise ValueError("El nodo origen y destino no pueden ser el mismo")
        if self._nodes.get_by_id(origin_id) is None:
            raise ValueError(f"Nodo origen con ID {origin_id} no encontrado")
        if self._nodes.get_by_id(destination_id) is None:
            raise ValueError(f"Nodo destino con ID {destination_id} no encontrado")

    @staticmethod
    def _validate_metrics(distance_km: float, capacity_gbps: float) -> None:
        if distance_km <= 0:
            raise ValueError("La distancia debe ser mayor a 0")
        if capacity_gbps <= 0:
            raise ValueError("La capacidad debe ser mayor a 0")

    def create_link(
        self,
        origin_id: int,
        destination_id: int,
        distance_km: float,
        capacity_gbps: float,
        status: str,
    ) -> FiberLink:
        self._validate_nodes(origin_id, destination_id)
        self._validate_metrics(distance_km, capacity_gbps)
        link = FiberLink(
            origin_node_id=origin_id,
            destination_node_id=destination_id,
            distance_km=distance_km,
            capacity_gbps=capacity_gbps,
            status=LinkStatus(status),
        )
        return self._links.create(link)

    def get_link(self, link_id: int) -> FiberLink:
        link = self._links.get_by_id(link_id)
        if link is None:
            raise ValueError(f"Enlace con ID {link_id} no encontrado")
        return link

    def get_all_links(self) -> List[FiberLink]:
        return self._links.get_all()

    def get_links_by_status(self, status: str) -> List[FiberLink]:
        return self._links.get_by_status(LinkStatus(status))

    def update_link(
        self,
        link_id: int,
        origin_id: int,
        destination_id: int,
        distance_km: float,
        capacity_gbps: float,
        status: str,
    ) -> FiberLink:
        link = self.get_link(link_id)
        self._validate_nodes(origin_id, destination_id)
        self._validate_metrics(distance_km, capacity_gbps)
        link.origin_node_id      = origin_id
        link.destination_node_id = destination_id
        link.distance_km         = distance_km
        link.capacity_gbps       = capacity_gbps
        link.status              = LinkStatus(status)
        return self._links.update(link)

    def delete_link(self, link_id: int) -> bool:
        self.get_link(link_id)
        if not self._links.delete(link_id):
            raise RuntimeError(f"No se pudo eliminar el enlace con ID {link_id}")
        return True
