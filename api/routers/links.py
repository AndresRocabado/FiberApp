from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from api.schemas import LinkCreate, LinkOut, LinkUpdate
from src.services.link_service import LinkService
from src.utils.csv_exporter import export_links_to_csv

router = APIRouter(prefix="/api/links", tags=["links"])
_svc   = LinkService()


@router.get("", response_model=list[LinkOut])
def list_links():
    links = _svc.get_all_links()
    return [_to_out(lnk) for lnk in links]


@router.get("/{link_id}", response_model=LinkOut)
def get_link(link_id: int):
    lnk = _svc.get_link(link_id)
    if not lnk:
        raise HTTPException(status_code=404, detail="Link not found")
    return _to_out(lnk)


@router.post("", response_model=LinkOut, status_code=201)
def create_link(body: LinkCreate):
    try:
        lnk = _svc.create_link(
            body.origin_node_id, body.destination_node_id,
            body.distance_km, body.capacity_gbps, body.status, body.name,
        )
        return _to_out(lnk)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{link_id}", response_model=LinkOut)
def update_link(link_id: int, body: LinkUpdate):
    try:
        lnk = _svc.update_link(
            link_id,
            body.origin_node_id, body.destination_node_id,
            body.distance_km, body.capacity_gbps, body.status, body.name,
        )
        return _to_out(lnk)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{link_id}", status_code=204)
def delete_link(link_id: int):
    try:
        _svc.delete_link(link_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/export/csv", response_class=PlainTextResponse)
def export_links():
    links = _svc.get_all_links()
    return PlainTextResponse(
        content=export_links_to_csv(links),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=enlaces.csv"},
    )


def _to_out(lnk) -> dict:
    return {
        "id":                    lnk.id,
        "name":                  lnk.name,
        "origin_node_id":        lnk.origin_node_id,
        "destination_node_id":   lnk.destination_node_id,
        "origin_node_name":      lnk.origin_node_name,
        "destination_node_name": lnk.destination_node_name,
        "distance_km":           lnk.distance_km,
        "capacity_gbps":         lnk.capacity_gbps,
        "status":                lnk.status.value,
        "created_at":            lnk.created_at,
    }
