import math
import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.modules.fog_of_war.repository import FogRepository
from app.modules.users.models import User

# Presence thresholds
MAX_ACCEPTABLE_ACCURACY_METERS = 100.0
MAX_PLAUSIBLE_SPEED_MPS = 50.0  # 180 km/h
MAX_TIMESTAMP_SKEW_SECONDS = 300.0  # 5 minutes


def get_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def validate_presence_report(
    lat: float,
    lon: float,
    accuracy: Optional[float] = None,
    client_timestamp: Optional[float] = None,
    last_accepted_location: Optional[Tuple[float, float, float]] = None,
) -> Tuple[bool, str]:
    if lat is None or lon is None or math.isnan(lat) or math.isnan(lon) or math.isinf(lat) or math.isinf(lon):
        return False, "مختصات جغرافیایی نامعتبر است."

    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        return False, "مختصات خارج از محدوده کره زمین است."

    if accuracy is not None:
        if accuracy < 0.0 or math.isnan(accuracy) or math.isinf(accuracy):
            return False, "شاخص دقت GPS نامعتبر است."
        if accuracy > MAX_ACCEPTABLE_ACCURACY_METERS:
            return False, f"دقت سیگنال موقعیت مکانی ({round(accuracy, 1)}m) برای ثبت کاوش ناکافی است."

    now = time.time()
    if client_timestamp is not None:
        if math.isnan(client_timestamp) or math.isinf(client_timestamp):
            return False, "زمان ثبت موقعیت مکانی نامعتبر است."
        skew = abs(now - client_timestamp)
        if skew > MAX_TIMESTAMP_SKEW_SECONDS:
            return False, "اختلاف زمانی گزارش موقعیت با سرور بیش از حد مجاز است."

    if last_accepted_location is not None:
        prev_lat, prev_lon, prev_ts = last_accepted_location
        dist = get_distance_meters(prev_lat, prev_lon, lat, lon)
        if client_timestamp is not None and prev_ts is not None:
            time_delta = client_timestamp - prev_ts
            if time_delta > 0.0:
                speed = dist / time_delta
                if speed > MAX_PLAUSIBLE_SPEED_MPS and dist > 5000.0:
                    return False, "سرعت جابجایی ثبت‌شده غیرواقعی است."

    return True, "موقعیت مکانی معتبر است."


def process_fog_discovery(
    db: Session,
    user_id: int,
    lat: float,
    lon: float,
    accuracy: Optional[float] = None,
    timestamp: Optional[float] = None,
) -> Dict[str, Any]:
    repo = FogRepository(db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Resilient auto-creation for test/guest user ids to satisfy foreign key
        user = User(id=user_id, username=f"user_{user_id}")
        db.add(user)
        try:
            db.commit()
        except Exception:
            db.rollback()

    # 1. Check user tracking setting
    if user and getattr(user, "exploration_tracking_enabled", True) is False:
        stats = repo.get_user_coverage_stats(user_id)
        disc_areas = repo.list_discovered_areas(user_id)
        return {
            "status": "paused",
            "message": "ردیابی کاوش غیرفعال است.",
            "current_points": len(disc_areas) * 10,
            "all_points": [{"lat": a.lat, "lon": a.lon} for a in disc_areas],
            "coverage_stats": stats,
        }

    # 2. Validate GPS presence
    last_areas = repo.list_discovered_areas(user_id)
    last_location = None
    if last_areas:
        last = last_areas[-1]
        last_ts = last.discovered_at.timestamp() if last.discovered_at else None
        last_location = (last.lat, last.lon, last_ts)

    is_valid, reason = validate_presence_report(
        lat=lat,
        lon=lon,
        accuracy=accuracy,
        client_timestamp=timestamp,
        last_accepted_location=last_location,
    )

    if not is_valid:
        stats = repo.get_user_coverage_stats(user_id)
        return {
            "status": "rejected",
            "message": reason,
            "current_points": len(last_areas) * 10,
            "all_points": [{"lat": a.lat, "lon": a.lon} for a in last_areas],
            "coverage_stats": stats,
        }

    # 3. Check for 50m proximity deduplication to avoid redundant buffer polygons
    is_duplicate = False
    for a in last_areas:
        if get_distance_meters(lat, lon, a.lat, a.lon) < 50.0:
            is_duplicate = True
            break

    if not is_duplicate:
        repo.create_discovered_area(user_id, lat, lon)
        repo.add_fog_discovery(user_id, lat, lon, radius_meters=150.0)
        repo.commit()

    all_areas = repo.list_discovered_areas(user_id)
    all_points = [{"lat": a.lat, "lon": a.lon} for a in all_areas]
    stats = repo.get_user_coverage_stats(user_id)

    msg = "منطقه جدید کشف شد!" if not is_duplicate else "مه به آرامی کنار رفت..."
    return {
        "status": "success",
        "message": msg,
        "current_points": len(all_areas) * 10,
        "all_points": all_points,
        "coverage_stats": stats,
    }


def get_fog_statistics(db: Session, user_id: int) -> Dict[str, Any]:
    repo = FogRepository(db)
    areas = repo.list_discovered_areas(user_id)
    stats = repo.get_user_coverage_stats(user_id)

    all_points = [{"lat": a.lat, "lon": a.lon} for a in areas]

    return {
        "user_id": user_id,
        "areas_discovered_count": len(all_points),
        "total_area_sqm": stats["total_area_sqm"],
        "total_area_sqkm": stats["total_area_sqkm"],
        "city_coverage_percentage": stats["city_coverage_percentage"],
        "all_points": all_points,
        "geojson_geometry": stats["geojson_geometry"],
    }
