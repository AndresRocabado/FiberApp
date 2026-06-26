from dataclasses import dataclass
from enum import Enum
from typing import Optional


class NodeType(str, Enum):
    CENTRAL      = "Central"
    DISTRIBUTION = "Distribución"
    ACCESS       = "Acceso"
    TERMINAL     = "Terminal"


class OperationalStatus(str, Enum):
    ACTIVE      = "Activo"
    INACTIVE    = "Inactivo"
    MAINTENANCE = "Mantenimiento"


@dataclass
class Node:
    name:      str
    city:      str
    node_type: NodeType
    status:    OperationalStatus
    id:         Optional[int] = None
    created_at: Optional[str] = None

    @classmethod
    def from_row(cls, row) -> "Node":
        return cls(
            id=row["id"],
            name=row["name"],
            city=row["city"],
            node_type=NodeType(row["node_type"]),
            status=OperationalStatus(row["status"]),
            created_at=row["created_at"],
        )
