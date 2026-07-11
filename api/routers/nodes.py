from fastapi import APIRouter, HTTPException
from fastapi.responses import PlainTextResponse

from api.schemas import NodeCreate, NodeOut, NodeUpdate
from src.services.node_service import NodeService
from src.utils.csv_exporter import export_nodes_to_csv

router = APIRouter(prefix="/api/nodes", tags=["nodes"])
_svc   = NodeService()


@router.get("", response_model=list[NodeOut])
def list_nodes():
    nodes = _svc.get_all_nodes()
    return [_to_out(n) for n in nodes]


@router.get("/cities")
def list_cities():
    return _svc.get_all_cities()


@router.get("/{node_id}", response_model=NodeOut)
def get_node(node_id: int):
    node = _svc.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return _to_out(node)


@router.post("", response_model=NodeOut, status_code=201)
def create_node(body: NodeCreate):
    try:
        node = _svc.create_node(body.name, body.city, body.node_type, body.status)
        return _to_out(node)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{node_id}", response_model=NodeOut)
def update_node(node_id: int, body: NodeUpdate):
    try:
        node = _svc.update_node(node_id, body.name, body.city, body.node_type, body.status)
        return _to_out(node)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{node_id}", status_code=204)
def delete_node(node_id: int):
    try:
        _svc.delete_node(node_id)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/export/csv", response_class=PlainTextResponse)
def export_nodes():
    nodes = _svc.get_all_nodes()
    return PlainTextResponse(
        content=export_nodes_to_csv(nodes),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=nodos.csv"},
    )


def _to_out(node) -> dict:
    return {
        "id":         node.id,
        "name":       node.name,
        "city":       node.city,
        "node_type":  node.node_type.value,
        "status":     node.status.value,
        "created_at": node.created_at,
    }
