from typing import Optional
from pydantic import BaseModel


class DualRouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: Optional[float] = None
    dest_lon: Optional[float] = None
    mood: Optional[str] = None


class WaypointInfo(BaseModel):
    name: str
    lat: float
    lon: float
    category: Optional[str] = ""


class DualRouteResponse(BaseModel):
    status: str
    message: str
    route_coordinates: list[list[float]]
    distance_meters: Optional[float] = 0.0
    duration_seconds: Optional[float] = 0.0
    waypoints: list[WaypointInfo] = []
