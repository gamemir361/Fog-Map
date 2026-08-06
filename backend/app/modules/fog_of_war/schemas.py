from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class LocationDiscover(BaseModel):
    user_id: Optional[int] = 1
    lat: float
    lon: float


class FogStatsResponse(BaseModel):
    user_id: int
    areas_discovered_count: int
    total_area_sqm: float
    total_area_sqkm: float
    city_coverage_percentage: float
    all_points: List[Dict[str, float]]
    geojson_geometry: Optional[Dict[str, Any]] = None