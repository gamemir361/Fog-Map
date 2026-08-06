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


def process_fog_discovery(db: Session, user_id: int, lat: float, lon: float):
    repo = FogRepository(db)
    user = db.query(User).filter(User.id == user_id).first()
    if user and getattr(user, "exploration_tracking_enabled", True) is False:
        all_discoveries = repo.get_user_centroids(user_id)
        stats = repo.get_user_coverage_stats(user_id)
        user_score = repo.get_or_create_user_score(user_id, 0)
        return {
            "status": "paused",
            "message": "ردیابی کاوش غیرفعال است.",
            "current_points": user_score.total_points,
            "all_points": [{"lat": p.lat, "lon": p.lon} for p in all_discoveries if p.lat is not None],
            "coverage_stats": stats,
        }

    previous_points = repo.get_user_centroids(user_id)

    should_give_points = True
    for pt in previous_points:
        if pt.lat is None or pt.lon is None:
            continue

        distance = get_distance_meters(lat, lon, pt.lat, pt.lon)
        if distance < 50.0:
            should_give_points = False
            break

    repo.add_fog_discovery(user_id, lat, lon, radius_meters=150.0)

    user_score = repo.get_or_create_user_score(user_id, 10 if should_give_points else 0)
    if should_give_points and user_score.id is not None:
        user_score.total_points += 10
        user_score.areas_discovered += 1

    repo.commit()

    all_discoveries = repo.get_user_centroids(user_id)
    stats = repo.get_user_coverage_stats(user_id)

    return {
        "status": "success",
        "message": "منطقه جدید با PostGIS کشف شد!" if should_give_points else "مه به آرامی کنار رفت...",
        "current_points": user_score.total_points,
        "all_points": [{"lat": p.lat, "lon": p.lon} for p in all_discoveries if p.lat is not None],
        "coverage_stats": stats,
    }


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
