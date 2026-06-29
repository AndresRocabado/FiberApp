import csv
import io
from typing import List

from src.models.link import FiberLink
from src.models.node import Node
from src.services.report_service import NetworkReport


def export_nodes_to_csv(nodes: List[Node]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=["id", "nombre", "ciudad", "tipo", "estado", "fecha_creacion"],
    )
    writer.writeheader()
    for n in nodes:
        writer.writerow({
            "id":             n.id,
            "nombre":         n.name,
            "ciudad":         n.city,
            "tipo":           n.node_type.value,
            "estado":         n.status.value,
            "fecha_creacion": n.created_at,
        })
    return output.getvalue()


def export_links_to_csv(links: List[FiberLink]) -> str:
    output = io.StringIO()
    writer = csv.DictWriter(
        output,
        fieldnames=[
            "id", "nombre", "nodo_origen", "nodo_destino",
            "distancia_km", "capacidad_gbps", "estado", "fecha_creacion",
        ],
    )
    writer.writeheader()
    for lnk in links:
        writer.writerow({
            "id":             lnk.id,
            "nombre":         lnk.name or "",
            "nodo_origen":    lnk.origin_node_name or lnk.origin_node_id,
            "nodo_destino":   lnk.destination_node_name or lnk.destination_node_id,
            "distancia_km":   lnk.distance_km,
            "capacidad_gbps": lnk.capacity_gbps,
            "estado":         lnk.status.value,
            "fecha_creacion": lnk.created_at,
        })
    return output.getvalue()


def export_report_to_csv(report: NetworkReport) -> str:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["Metrica", "Valor"])
    writer.writerow(["Total de Nodos",                report.total_nodes])
    writer.writerow(["Total de Enlaces",              report.total_links])
    writer.writerow(["Fibra Total (km)",              report.total_fiber_km])
    writer.writerow(["Enlaces Activos",               report.active_links])
    writer.writerow(["Enlaces Inactivos",             report.inactive_links])
    writer.writerow(["Enlaces en Mantenimiento",      report.maintenance_links])
    writer.writerow([])
    writer.writerow(["Ciudad", "Cantidad de Nodos"])
    for city, count in report.nodes_by_city.items():
        writer.writerow([city, count])

    return output.getvalue()
