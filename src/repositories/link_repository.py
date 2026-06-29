from typing import List, Optional

from database.connection import get_connection
from src.models.link import FiberLink, LinkStatus
from src.repositories.base_repository import BaseRepository

_SELECT_WITH_NAMES = """
    SELECT fl.*,
           n1.name AS origin_node_name,
           n2.name AS destination_node_name
    FROM   fiber_links fl
    JOIN   nodes n1 ON fl.origin_node_id      = n1.id
    JOIN   nodes n2 ON fl.destination_node_id = n2.id
"""


class LinkRepository(BaseRepository[FiberLink]):

    def create(self, link: FiberLink) -> FiberLink:
        sql = """
            INSERT INTO fiber_links
                (origin_node_id, destination_node_id, distance_km, capacity_gbps, status, name)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        with get_connection() as conn:
            cursor = conn.execute(sql, (
                link.origin_node_id, link.destination_node_id,
                link.distance_km, link.capacity_gbps, link.status.value, link.name,
            ))
            link.id = cursor.lastrowid
        return link

    def get_by_id(self, link_id: int) -> Optional[FiberLink]:
        sql = _SELECT_WITH_NAMES + " WHERE fl.id = ?"
        with get_connection() as conn:
            row = conn.execute(sql, (link_id,)).fetchone()
        return FiberLink.from_row(row) if row else None

    def get_all(self) -> List[FiberLink]:
        sql = _SELECT_WITH_NAMES + " ORDER BY fl.id"
        with get_connection() as conn:
            rows = conn.execute(sql).fetchall()
        return [FiberLink.from_row(r) for r in rows]

    def get_by_status(self, status: LinkStatus) -> List[FiberLink]:
        sql = _SELECT_WITH_NAMES + " WHERE fl.status = ? ORDER BY fl.id"
        with get_connection() as conn:
            rows = conn.execute(sql, (status.value,)).fetchall()
        return [FiberLink.from_row(r) for r in rows]

    def get_by_node(self, node_id: int) -> List[FiberLink]:
        sql = _SELECT_WITH_NAMES + " WHERE fl.origin_node_id = ? OR fl.destination_node_id = ?"
        with get_connection() as conn:
            rows = conn.execute(sql, (node_id, node_id)).fetchall()
        return [FiberLink.from_row(r) for r in rows]

    def update(self, link: FiberLink) -> FiberLink:
        sql = """
            UPDATE fiber_links
            SET origin_node_id = ?, destination_node_id = ?,
                distance_km = ?, capacity_gbps = ?, status = ?, name = ?
            WHERE id = ?
        """
        with get_connection() as conn:
            conn.execute(sql, (
                link.origin_node_id, link.destination_node_id,
                link.distance_km, link.capacity_gbps, link.status.value, link.name, link.id,
            ))
        return link

    def delete(self, link_id: int) -> bool:
        with get_connection() as conn:
            cursor = conn.execute("DELETE FROM fiber_links WHERE id = ?", (link_id,))
            return cursor.rowcount > 0
