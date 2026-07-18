from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class NodeCreate(BaseModel):
    name:      str
    city:      str
    node_type: str
    status:    str


class NodeUpdate(BaseModel):
    name:      str
    city:      str
    node_type: str
    status:    str


class NodeOut(BaseModel):
    id:         int
    name:       str
    city:       str
    node_type:  str
    status:     str
    created_at: Optional[str] = None


class LinkCreate(BaseModel):
    origin_node_id:      int
    destination_node_id: int
    distance_km:         float = Field(gt=0)
    capacity_gbps:       float = Field(gt=0)
    status:              str
    name:                Optional[str] = None


class LinkUpdate(BaseModel):
    origin_node_id:      int
    destination_node_id: int
    distance_km:         float = Field(gt=0)
    capacity_gbps:       float = Field(gt=0)
    status:              str
    name:                Optional[str] = None


class LinkOut(BaseModel):
    id:                   int
    name:                 Optional[str]
    origin_node_id:       int
    destination_node_id:  int
    origin_node_name:     Optional[str]
    destination_node_name: Optional[str]
    distance_km:          float
    capacity_gbps:        float
    status:               str
    created_at:           Optional[str] = None


class ReportOut(BaseModel):
    total_nodes:       int
    total_links:       int
    total_fiber_km:    float
    active_links:      int
    inactive_links:    int
    maintenance_links: int
    nodes_by_city:     dict
