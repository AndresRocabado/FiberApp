from typing import List, Optional

from database.connection import get_connection
from src.models.node import Node, NodeType, OperationalStatus
from src.repositories.base_repository import BaseRepository


class NodeRepository(BaseRepository[Node]):

    def create(self, node: Node) -> Node:
        sql = "INSERT INTO nodes (name, city, node_type, status) VALUES (?, ?, ?, ?)"
        with get_connection() as conn:
            cursor = conn.execute(sql, (node.name, node.city, node.node_type.value, node.status.value))
            node.id = cursor.lastrowid
        return node

    def get_by_id(self, node_id: int) -> Optional[Node]:
        with get_connection() as conn:
            row = conn.execute("SELECT * FROM nodes WHERE id = ?", (node_id,)).fetchone()
        return Node.from_row(row) if row else None

    def get_all(self) -> List[Node]:
        with get_connection() as conn:
            rows = conn.execute("SELECT * FROM nodes ORDER BY name").fetchall()
        return [Node.from_row(r) for r in rows]

    def get_by_city(self, city: str) -> List[Node]:
        with get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM nodes WHERE city = ? ORDER BY name", (city,)
            ).fetchall()
        return [Node.from_row(r) for r in rows]

    def update(self, node: Node) -> Node:
        sql = "UPDATE nodes SET name = ?, city = ?, node_type = ?, status = ? WHERE id = ?"
        with get_connection() as conn:
            conn.execute(sql, (node.name, node.city, node.node_type.value, node.status.value, node.id))
        return node

    def delete(self, node_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
            return cursor.rowcount > 0

    def exists_by_name(self, name: str, exclude_id: Optional[int] = None) -> bool:
        if exclude_id is not None:
            sql = "SELECT 1 FROM nodes WHERE name = ? AND id != ?"
            args = (name, exclude_id)
        else:
            sql = "SELECT 1 FROM nodes WHERE name = ?"
            args = (name,)
        with get_connection() as conn:
            return conn.execute(sql, args).fetchone() is not None
