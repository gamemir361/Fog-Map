from typing import Any, Optional
from pydantic import BaseModel


class POIResponse(BaseModel):
    id: int
    name: str
    category: str
    lat: float
    lon: float
    description: str = ""
    vectors: dict[str, float] = {}
    match_percentage: Optional[float] = None
    is_discovered: bool = False
    discovery_state: str = "unknown"
    discovered_at: Optional[str] = None
    discovery_source: Optional[str] = None
    rarity: str = "common"
    poi_type: str = "standard"
    is_secret: bool = False
    expires_at: Optional[str] = None

    class Config:
        from_attributes = True


class FogDiscoverRequest(BaseModel):
    user_id: int = 1
    lat: float
    lon: float


class FogDiscoverResponse(BaseModel):
    status: Optional[str] = "success"
    message: str
    current_points: int
    all_points: list[dict[str, float]]
    user_preferences: Optional[dict[str, float]] = None
    progression: Optional[dict[str, Any]] = None
    xp_feedback: Optional[dict[str, Any]] = None


class RoutePlanRequest(BaseModel):
    lat: float
    lon: float
    mood: str


class RoutePlanResponse(BaseModel):
    status: str
    message: str
    route_coordinates: list[list[float]]