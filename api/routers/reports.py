from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from api.schemas import ReportOut
from src.services.report_service import ReportService
from src.utils.csv_exporter import export_report_to_csv

router = APIRouter(prefix="/api/reports", tags=["reports"])
_svc   = ReportService()


@router.get("", response_model=ReportOut)
def get_report():
    r = _svc.generate_report()
    return {
        "total_nodes":       r.total_nodes,
        "total_links":       r.total_links,
        "total_fiber_km":    r.total_fiber_km,
        "active_links":      r.active_links,
        "inactive_links":    r.inactive_links,
        "maintenance_links": r.maintenance_links,
        "nodes_by_city":     r.nodes_by_city,
    }


@router.get("/export/csv", response_class=PlainTextResponse)
def export_report():
    r = _svc.generate_report()
    return PlainTextResponse(
        content=export_report_to_csv(r),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=reporte_red.csv"},
    )
