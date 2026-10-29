from dataclasses import dataclass, field
from typing import Dict, List

from database.connection import get_connection


@dataclass
class NetworkReport:
    total_nodes:        int
    total_links:        int
    total_fiber_km:     float
    nodes_by_city:      Dict[str, int]
    active_links:       int
    inactive_links:     int
    maintenance_links:  int
    isolated_nodes:     List[Dict] = field(default_factory=list)  # active nodes with no active links


class ReportService:
    def generate_report(self) -> NetworkReport:
        with get_connection() as conn:
            total_nodes = conn.execute(
                "SELECT COUNT(*) FROM nodes WHERE deleted_at IS NULL"
            ).fetchone()[0]
            total_links, total_km, active, inactive, maintenance = conn.execute("""
                SELECT COUNT(*),
                       COALESCE(SUM(distance_km), 0),
                       COALESCE(SUM(status = 'Activo'), 0),
                       COALESCE(SUM(status = 'Inactivo'), 0),
                       COALESCE(SUM(status = 'Mantenimiento'), 0)
                FROM   fiber_links
                WHERE  deleted_at IS NULL
            """).fetchone()

            city_rows = conn.execute(
                "SELECT city, COUNT(*) AS cnt FROM nodes WHERE deleted_at IS NULL GROUP BY city ORDER BY cnt DESC"
            ).fetchall()
            nodes_by_city = {r["city"]: r["cnt"] for r in city_rows}

            isolated_rows = conn.execute("""
                SELECT id, name, city FROM nodes n
                WHERE  n.deleted_at IS NULL
                  AND  NOT EXISTS (
                      SELECT 1 FROM fiber_links fl
                      WHERE  fl.deleted_at IS NULL
                        AND  (fl.origin_node_id = n.id OR fl.destination_node_id = n.id)
                  )
                ORDER BY n.name
            """).fetchall()
            isolated_nodes = [dict(r) for r in isolated_rows]

        return NetworkReport(
            total_nodes=total_nodes,
            total_links=total_links,
            total_fiber_km=round(float(total_km), 2),
            nodes_by_city=nodes_by_city,
            active_links=active,
            inactive_links=inactive,
            maintenance_links=maintenance,
            isolated_nodes=isolated_nodes,
        )
