import math
from sqlalchemy.orm import Session

from app.modules.fog_of_war.repository import FogRepository


def get_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


from app.modules.users.models import User


from app.modules.exploration.service import discover_fog


def process_fog_discovery(db: Session, user_id: int, lat: float, lon: float):
    """
    Canonical Fog Discovery delegate.
    Routes through the unified discovery pipeline (Exploration + PostGIS + XPEngine).
    """
    return discover_fog(db, user_id, lat, lon)


from app.modules.exploration.repository import ExplorationRepository


def get_fog_statistics(db: Session, user_id: int):
    repo = FogRepository(db)
    exp_repo = ExplorationRepository(db)

    centroids = repo.get_user_centroids(user_id)
    stats = repo.get_user_coverage_stats(user_id)
    disc_areas = exp_repo.list_discovered_areas(user_id)

    all_pts_set = set()
    all_points = []

    for c in centroids:
        if c.lat is not None and c.lon is not None:
            key = (round(c.lat, 5), round(c.lon, 5))
            if key not in all_pts_set:
                all_pts_set.add(key)
                all_points.append({"lat": c.lat, "lon": c.lon})

    for a in disc_areas:
        if a.lat is not None and a.lon is not None:
            key = (round(a.lat, 5), round(a.lon, 5))
            if key not in all_pts_set:
                all_pts_set.add(key)
                all_points.append({"lat": a.lat, "lon": a.lon})

    count = max(len(centroids), len(disc_areas), len(all_points))

    return {
        "user_id": user_id,
        "areas_discovered_count": count,
        "total_area_sqm": stats["total_area_sqm"],
        "total_area_sqkm": stats["total_area_sqkm"],
        "city_coverage_percentage": stats["city_coverage_percentage"],
        "all_points": all_points,
        "geojson_geometry": stats["geojson_geometry"],
    }
