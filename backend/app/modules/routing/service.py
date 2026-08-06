import math
import requests
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from app.modules.routing.repository import RoutingRepository


def haversine_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


def get_osrm_route(coords):
    if len(coords) < 2:
        return coords, 0.0, 0.0

    coords_str = ";".join([f"{lon},{lat}" for lat, lon in coords])
    url = f"http://router.project-osrm.org/route/v1/foot/{coords_str}?overview=full&geometries=geojson"

    try:
        response = requests.get(url, timeout=4)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "Ok":
                route = data["routes"][0]
                geometry = route["geometry"]["coordinates"]
                distance = route.get("distance", 0.0)
                duration = route.get("duration", 0.0)
                return [[lat, lon] for lon, lat in geometry], distance, duration
    except Exception as exc:
        print(f"⚠️ OSRM API Fallback triggered: {exc}")

    # Straight-line Fallback if OSRM is offline or timed out
    total_dist = 0.0
    for i in range(len(coords) - 1):
        total_dist += haversine_distance_meters(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
    est_duration = (total_dist / 1.4)  # ~1.4 m/s walking speed

    return coords, total_dist, est_duration


def plan_dual_route(
    db: Session,
    origin_lat: float,
    origin_lon: float,
    dest_lat: float = None,
    dest_lon: float = None,
    mood: str = None,
):
    repo = RoutingRepository(db)
    waypoints_data = []
    points_to_visit = [[origin_lat, origin_lon]]

    best_vibe_poi = None
    if mood and mood != 'direct':
        vibe_pois = repo.get_pois_for_mood(mood, limit=2)
        if vibe_pois:
            best_vibe_poi = vibe_pois[0]
            pt = to_shape(best_vibe_poi.geometry)
            points_to_visit.append([pt.y, pt.x])
            waypoints_data.append({
                "name": best_vibe_poi.name,
                "lat": pt.y,
                "lon": pt.x,
                "category": best_vibe_poi.category or "",
            })

    if dest_lat is not None and dest_lon is not None:
        points_to_visit.append([dest_lat, dest_lon])
    elif best_vibe_poi is None:
        # Fallback destination if neither dest nor mood provided
        all_pois = repo.db.query(repo.POI).limit(1).all()
        if all_pois:
            pt = to_shape(all_pois[0].geometry)
            points_to_visit.append([pt.y, pt.x])
            waypoints_data.append({
                "name": all_pois[0].name,
                "lat": pt.y,
                "lon": pt.x,
                "category": all_pois[0].category or "",
            })

    final_route, distance, duration = get_osrm_route(points_to_visit)

    mood_messages = {
        "nature": "مسیر طبیعت‌گردی سرسبز و دلپذیر آماده شد! 🌲",
        "culture": "مسیر تاریخی-فرهنگی هوشمند آماده شد! 🏛️",
        "energy": "مسیر پرانرژی و جذاب آماده شد! ⚡",
        "quiet": "مسیر دنج و آرامش‌بخش آماده شد! ☕",
        "photography": "مسیر عکاسی با بهترین زاویه‌های دید آماده شد! 📸",
        "nightlife": "مسیر شب‌گردی رویایی پایتخت آماده شد! 🌌",
    }
    msg = mood_messages.get(mood, "مسیر پیاده‌روی مستقیم و هوشمند ایجاد شد! 🧭")

    return {
        "status": "success",
        "message": msg,
        "route_coordinates": final_route,
        "distance_meters": round(distance, 1),
        "duration_seconds": round(duration, 1),
        "waypoints": waypoints_data,
    }


def plan_mood_route(db: Session, lat: float, lon: float, mood: str):
    res = plan_dual_route(db, origin_lat=lat, origin_lon=lon, mood=mood)
    return {
        "status": res["status"],
        "message": res["message"],
        "route_coordinates": res["route_coordinates"],
        "waypoints_visited": [w["name"] for w in res["waypoints"]],
    }
