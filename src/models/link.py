from dataclasses import dataclass
from enum import Enum
from typing import Optional


class LinkStatus(str, Enum):
    ACTIVE      = "Activo"
    INACTIVE    = "Inactivo"
    MAINTENANCE = "Mantenimiento"


@dataclass
class FiberLink:
    origin_node_id:      int
    destination_node_id: int
    distance_km:         float
    capacity_gbps:       float
    status:              LinkStatus
    name:                  Optional[str] = None
    id:                    Optional[int] = None
    created_at:            Optional[str] = None
    origin_node_name:      Optional[str] = None
    destination_node_name: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "FiberLink":
        keys = row.keys()
        return cls(
            id=row["id"],
            origin_node_id=row["origin_node_id"],
            destination_node_id=row["destination_node_id"],
            distance_km=row["distance_km"],
            capacity_gbps=row["capacity_gbps"],
            status=LinkStatus(row["status"]),
            name=row["name"] if "name" in row.keys() else None,
            created_at=row["created_at"],
            origin_node_name=row["origin_node_name"] if "origin_node_name" in keys else None,
            destination_node_name=row["destination_node_name"] if "destination_node_name" in keys else None,
        )
