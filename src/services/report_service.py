from dataclasses import dataclass, field
from typing import Dict

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


class ReportService:
    def generate_report(self) -> NetworkReport:
        with get_connection() as conn:
            total_nodes = conn.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
            total_links = conn.execute("SELECT COUNT(*) FROM fiber_links").fetchone()[0]
            total_km    = conn.execute(
                "SELECT COALESCE(SUM(distance_km), 0) FROM fiber_links"
            ).fetchone()[0]

            city_rows = conn.execute(
                "SELECT city, COUNT(*) AS cnt FROM nodes GROUP BY city ORDER BY cnt DESC"
            ).fetchall()
            nodes_by_city = {r["city"]: r["cnt"] for r in city_rows}

            def count_links(status: str) -> int:
                return conn.execute(
                    "SELECT COUNT(*) FROM fiber_links WHERE status = ?", (status,)
                ).fetchone()[0]

            active      = count_links("Activo")
            inactive    = count_links("Inactivo")
            maintenance = count_links("Mantenimiento")

        return NetworkReport(
            total_nodes=total_nodes,
            total_links=total_links,
            total_fiber_km=round(float(total_km), 2),
            nodes_by_city=nodes_by_city,
            active_links=active,
            inactive_links=inactive,
            maintenance_links=maintenance,
        )
