import math
import random
import datetime
import requests
from typing import Optional, List, Dict, Any
from geoalchemy2.shape import to_shape

from app.core.config.poi_config import POI_DISCOVERY_CONFIG
from app.modules.exploration.models import DiscoveredArea, POI, User, UserPOIDiscovery, UserPOIState
from app.modules.exploration.repository import ExplorationRepository
from app.modules.gamification.xp_engine import XPEngine
from app.modules.missions.service import update_user_missions

VIBE_FIELDS = [
    ("pref_nature", "nature"),
    ("pref_history", "history"),
    ("pref_crowded", "crowded"),
    ("pref_quiet", "quiet"),
    ("pref_nightlife", "nightlife"),
    ("pref_luxury", "luxury"),
    ("pref_budget", "budget"),
    ("pref_romantic", "romantic"),
    ("pref_family", "family"),
    ("pref_study", "study"),
    ("pref_photography", "photography"),
    ("pref_food", "food"),
]


def initialize_user_poi_states(db, user_id: int):
    """
    Phase 3 — Initial Distribution:
    Generates 30% Hidden and 70% Unknown initial state distribution ONCE per user.
    Never regenerates state for an existing user across logins, refreshes, or restarts.
    """
    existing_count = db.query(UserPOIState).filter(UserPOIState.user_id == user_id).count()
    if existing_count > 0:
        return

    pois = db.query(POI).order_by(POI.id.asc()).all()
    if not pois:
        return

    total = len(pois)
    hidden_pct = POI_DISCOVERY_CONFIG.get("DEFAULT_HIDDEN_PERCENT", 0.30)
    num_hidden = int(round(total * hidden_pct))

    # Deterministic user-seeded shuffle so each user gets a unique permanent initial distribution
    rng = random.Random(user_id)
    shuffled_indices = list(range(total))
    rng.shuffle(shuffled_indices)
    hidden_set = set(shuffled_indices[:num_hidden])

    new_states = []
    for idx, poi in enumerate(pois):
        state = "hidden" if idx in hidden_set else "unknown"
        new_states.append(
            UserPOIState(
                user_id=user_id,
                poi_id=poi.id,
                state=state,
                discovery_source="system_init",
                discovery_version=1,
            )
        )

    if new_states:
        db.bulk_save_objects(new_states)
        db.commit()


def build_poi_payload(
    poi,
    match_percentage: float = None,
    discovery_state: str = "discovered",
    discovered_at: Optional[datetime.datetime] = None,
    discovery_source: Optional[str] = None,
):
    """
    Builds POI response dict based on user discovery state:
    - HIDDEN (Phase 4): Completely masked. (Filtered out before output).
    - UNKNOWN (Phase 5): Category, name, description, vectors masked as Unknown Mystery POI.
    - DISCOVERED (Phase 6): Fully revealed with real metadata and categories.
    """
    point = getattr(poi, "geometry", None)
    if point is None:
        lat = 0.0
        lon = 0.0
    else:
        try:
            shape = to_shape(point)
            lat = getattr(shape, "y", 0.0)
            lon = getattr(shape, "x", 0.0)
        except Exception:
            lat = getattr(point, "y", 0.0)
            lon = getattr(point, "x", 0.0)

    rarity = getattr(poi, "rarity", "common") or "common"
    poi_type = getattr(poi, "poi_type", "standard") or "standard"
    is_secret = getattr(poi, "is_secret", False) or False
    expires_at = getattr(poi, "expires_at", None)
    expires_at_str = expires_at.isoformat() if expires_at else None
    discovered_at_str = discovered_at.isoformat() if discovered_at else None

    if discovery_state == "hidden":
        return {
            "id": getattr(poi, "id", None),
            "name": "مکان مخفی",
            "category": "hidden",
            "lat": lat,
            "lon": lon,
            "description": "",
            "vectors": {},
            "is_discovered": False,
            "discovery_state": "hidden",
            "discovered_at": None,
            "discovery_source": None,
            "rarity": rarity,
            "poi_type": poi_type,
            "is_secret": is_secret,
            "expires_at": expires_at_str,
        }

    if discovery_state == "unknown":
        return {
            "id": getattr(poi, "id", None),
            "name": "مکان ناشناخته",
            "category": "unknown",
            "lat": lat,
            "lon": lon,
            "description": "این مکان هنوز کشف نشده است. برای کشف آن به محدوده نزدیک شوید!",
            "vectors": {},
            "is_discovered": False,
            "discovery_state": "unknown",
            "discovered_at": None,
            "discovery_source": None,
            "rarity": rarity,
            "poi_type": poi_type,
            "is_secret": is_secret,
            "expires_at": expires_at_str,
        }

    details = getattr(poi, "details", None)
    if details is None:
        vectors = {}
        description = ""
    else:
        vectors = {
            "nature": getattr(details, "nature", 0.0),
            "history": getattr(details, "history", 0.0),
            "crowded": getattr(details, "crowded", 0.0),
            "quiet": getattr(details, "quiet", 0.0),
            "nightlife": getattr(details, "nightlife", 0.0),
            "luxury": getattr(details, "luxury", 0.0),
            "budget": getattr(details, "budget", 0.0),
            "romantic": getattr(details, "romantic", 0.0),
            "family": getattr(details, "family", 0.0),
            "study": getattr(details, "study", 0.0),
            "photography": getattr(details, "photography", 0.0),
            "food": getattr(details, "food", 0.0),
        }
        description = getattr(details, "description", "")

    payload = {
        "id": getattr(poi, "id", None),
        "name": getattr(poi, "name", ""),
        "category": getattr(poi, "category", ""),
        "lat": lat,
        "lon": lon,
        "description": description,
        "vectors": vectors,
        "is_discovered": True,
        "discovery_state": "discovered",
        "discovered_at": discovered_at_str,
        "discovery_source": discovery_source or "gps",
        "rarity": rarity,
        "poi_type": poi_type,
        "is_secret": is_secret,
        "expires_at": expires_at_str,
    }
    if match_percentage is not None:
        payload["match_percentage"] = match_percentage

    return payload


def get_user_preference_vector(user):
    return {vibe: round(getattr(user, pref, 0.5), 4) for pref, vibe in VIBE_FIELDS}


def get_dominant_user_vibes(user, top_k: int = 3):
    pref_vec = get_user_preference_vector(user)
    sorted_vibes = sorted(pref_vec.items(), key=lambda item: item[1], reverse=True)
    return [vibe for vibe, _ in sorted_vibes[:top_k]]


def compute_recommendation_score(user, detail):
    raw_score = sum(
        getattr(user, pref_name, 0.5) * getattr(detail, detail_name, 0.0)
        for pref_name, detail_name in VIBE_FIELDS
    )
    user_magnitude = math_norm([getattr(user, p, 0.5) for p, _ in VIBE_FIELDS])
    detail_magnitude = math_norm([getattr(detail, d, 0.0) for _, d in VIBE_FIELDS])

    if user_magnitude > 0 and detail_magnitude > 0:
        cosine_sim = raw_score / (user_magnitude * detail_magnitude)
        return round(min(100.0, max(0.0, cosine_sim * 100)), 1)

    return round(raw_score * 10.0, 1)


def math_norm(vec):
    return (sum(v * v for v in vec)) ** 0.5


def apply_discovery_preferences(user, detail, alpha=0.2):
    for pref_name, detail_name in VIBE_FIELDS:
        current_val = getattr(user, pref_name, 0.5)
        detail_val = getattr(detail, detail_name, 0.0)
        updated_val = (current_val * (1 - alpha)) + (detail_val * alpha)
        setattr(user, pref_name, round(updated_val, 4))

    return user


def build_discovery_message(score_delta, discovered_name):
    return f"منطقه جدید کشف شد! +{score_delta} XP 🧭 ({discovered_name})"


def get_poi_lat_lon(poi):
    point = getattr(poi, "geometry", None)
    if point is None:
        return 0.0, 0.0
    try:
        shape = to_shape(point)
        return getattr(shape, "y", 0.0), getattr(shape, "x", 0.0)
    except Exception:
        return getattr(point, "y", 0.0), getattr(point, "x", 0.0)


def list_pois(
    db,
    category: str = None,
    search: str = None,
    bbox: str = None,
    limit: int = 100,
    offset: int = 0,
    user_id: Optional[int] = None,
):
    """
    Phase 7 & 8 POI Listing, Map Filtering, and Search logic:
    - HIDDEN POIs: NEVER appear anywhere in output, search, or filters.
    - UNKNOWN POIs: Appear in 'All' and 'Unknown' filters. Hidden from category filters and search.
    - DISCOVERED POIs: Appear in 'All', category filters, and search.
    """
    repository = ExplorationRepository(db)

    state_map = {}
    if user_id is not None:
        initialize_user_poi_states(db, user_id)

        user_areas = db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id).all()
        user_coords = [(a.lat, a.lon) for a in user_areas if a.lat is not None and a.lon is not None]

        user_states = db.query(UserPOIState).filter(UserPOIState.user_id == user_id).all()
        state_map = {s.poi_id: s for s in user_states}

        # Auto-discover POIs near user's explored fog areas
        all_pois_db = repository.list_pois(limit=1000)
        state_updated = False
        for poi in all_pois_db:
            plat, plon = get_poi_lat_lon(poi)
            st_rec = state_map.get(poi.id)
            if st_rec and st_rec.state != "discovered":
                for alat, alon in user_coords:
                    if get_distance_meters(alat, alon, plat, plon) <= POI_DISCOVERY_CONFIG.get("DISCOVERY_RADIUS_METERS", 200.0):
                        st_rec.state = "discovered"
                        st_rec.discovered_at = datetime.datetime.utcnow()
                        st_rec.discovery_source = "gps"
                        XPEngine.award_xp(db, user_id, "DISCOVER_POI", entity_id=f"poi_{poi.id}")
                        state_updated = True
                        break

        if state_updated:
            db.commit()
            user_states = db.query(UserPOIState).filter(UserPOIState.user_id == user_id).all()
            state_map = {s.poi_id: s for s in user_states}

    # Query POIs from Repository
    pois = repository.list_pois(
        category=category if category not in ("unknown", "all", "all_pois", None) else None,
        search=search,
        bbox=bbox,
        limit=limit,
        offset=offset,
    )

    res = []
    for poi in pois:
        if user_id is not None:
            st_rec = state_map.get(poi.id)
            cur_state = st_rec.state if st_rec else "unknown"
            disc_at = st_rec.discovered_at if st_rec else None
            disc_src = st_rec.discovery_source if st_rec else None

            # Phase 4 Rule: Hidden POIs NEVER appear anywhere!
            if cur_state == "hidden":
                continue

            # Phase 7 Filter Rules
            if category == "unknown":
                # Unknown filter: ONLY show Unknown markers
                if cur_state != "unknown":
                    continue
            elif category and category.lower() not in ("all", "all_pois"):
                # Specific category filter (e.g. cafe, nature): ONLY show Discovered POIs
                if cur_state != "discovered":
                    continue
            elif search:
                # Phase 8 Search Rule: Search ONLY returns Discovered POIs
                if cur_state != "discovered":
                    continue

            payload = build_poi_payload(
                poi,
                discovery_state=cur_state,
                discovered_at=disc_at,
                discovery_source=disc_src,
            )
            res.append(payload)
        else:
            # Unauthenticated legacy / fallback mode
            res.append(build_poi_payload(poi, discovery_state="discovered"))

    return res


def get_distance_meters(lat1, lon1, lat2, lon2):
    R = 6371000.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


from app.modules.fog_of_war.repository import FogRepository


def discover_fog(db, user_id, lat, lon, xp_reward=None):
    try:
        repository = ExplorationRepository(db)
        fog_repo = FogRepository(db)
        user = repository.get_user_by_id(user_id)
        if not user:
            user = repository.create_user(user_id)

        if getattr(user, "exploration_tracking_enabled", True) is False:
            disc_areas = repository.list_discovered_areas(user.id)
            centroids = fog_repo.get_user_centroids(user.id)
            all_pts_set = set()
            all_points = []
            for a in disc_areas:
                if a.lat is not None and a.lon is not None:
                    key = (round(a.lat, 5), round(a.lon, 5))
                    if key not in all_pts_set:
                        all_pts_set.add(key)
                        all_points.append({"lat": a.lat, "lon": a.lon})
            for c in centroids:
                if c.lat is not None and c.lon is not None:
                    key = (round(c.lat, 5), round(c.lon, 5))
                    if key not in all_pts_set:
                        all_pts_set.add(key)
                        all_points.append({"lat": c.lat, "lon": c.lon})

            progression = XPEngine.calculate_progression(user.score or 0)
            return {
                "status": "paused",
                "message": "ردیابی کاوش غیرفعال است. هیچ منطقه یا امتیازی ثبت نشد.",
                "current_points": user.score or 0,
                "all_points": all_points,
                "progression": progression,
                "xp_feedback": {
                    "badge": "+0 XP",
                    "reason": "ردیابی غیرفعال",
                    "level_up": False,
                },
                "data": {
                    "current_points": user.score or 0,
                    "all_points": all_points,
                },
                "user_preferences": get_user_preference_vector(user),
            }

        previous_areas = repository.list_discovered_areas(user.id)
        should_give_points = True
        for area in previous_areas:
            if area.lat is not None and area.lon is not None:
                if get_distance_meters(lat, lon, area.lat, area.lon) < 50.0:
                    should_give_points = False
                    break

        repository.create_discovered_area(user.id, lat, lon)
        fog_repo.add_fog_discovery(user.id, lat, lon, radius_meters=150.0)

        # 🎯 Award XP via Central XPEngine
        xp_res = None
        if should_give_points:
            area_entity_id = f"area_{round(lat, 3)}_{round(lon, 3)}"
            xp_res = XPEngine.award_xp(
                db, user.id, "DISCOVER_AREA", entity_id=area_entity_id, custom_xp=xp_reward
            )
        else:
            progression = XPEngine.calculate_progression(user.score or 0)
            xp_res = {
                "xp_earned": 0,
                "status": "duplicate",
                "message": "مه به آرامی کنار رفت...",
                "is_duplicate": True,
                "progression": progression,
                "feedback": {"badge": "+0 XP", "reason": "منطقه تکراری", "level_up": False},
            }

        # Check all POIs within 200m of this discovered point
        all_pois = repository.list_pois(limit=500)
        learned_vibe_name = ""
        poi_xp_res = None

        initialize_user_poi_states(db, user.id)

        for p in all_pois:
            plat, plon = get_poi_lat_lon(p)
            if get_distance_meters(lat, lon, plat, plon) <= POI_DISCOVERY_CONFIG.get("DISCOVERY_RADIUS_METERS", 200.0):
                st_rec = (
                    db.query(UserPOIState)
                    .filter(UserPOIState.user_id == user.id, UserPOIState.poi_id == p.id)
                    .first()
                )
                if not st_rec:
                    st_rec = UserPOIState(
                        user_id=user.id,
                        poi_id=p.id,
                        state="discovered",
                        discovered_at=datetime.datetime.utcnow(),
                        discovery_source="gps",
                    )
                    db.add(st_rec)
                    poi_xp_res = XPEngine.award_xp(db, user.id, "DISCOVER_POI", entity_id=f"poi_{p.id}")
                elif st_rec.state != "discovered":
                    st_rec.state = "discovered"
                    st_rec.discovered_at = datetime.datetime.utcnow()
                    st_rec.discovery_source = "gps"
                    poi_xp_res = XPEngine.award_xp(db, user.id, "DISCOVER_POI", entity_id=f"poi_{p.id}")

                existing_disc = (
                    db.query(UserPOIDiscovery)
                    .filter(UserPOIDiscovery.user_id == user.id, UserPOIDiscovery.poi_id == p.id)
                    .first()
                )
                if not existing_disc:
                    db.add(UserPOIDiscovery(user_id=user.id, poi_id=p.id))

                if p.details:
                    apply_discovery_preferences(user, p.details, alpha=0.2)
                    learned_vibe_name = p.name

        db.commit()
        db.refresh(user)

        disc_areas = repository.list_discovered_areas(user.id)
        centroids = fog_repo.get_user_centroids(user.id)

        all_pts_set = set()
        all_points = []
        for a in disc_areas:
            if a.lat is not None and a.lon is not None:
                key = (round(a.lat, 5), round(a.lon, 5))
                if key not in all_pts_set:
                    all_pts_set.add(key)
                    all_points.append({"lat": a.lat, "lon": a.lon})

        for c in centroids:
            if c.lat is not None and c.lon is not None:
                key = (round(c.lat, 5), round(c.lon, 5))
                if key not in all_pts_set:
                    all_pts_set.add(key)
                    all_points.append({"lat": c.lat, "lon": c.lon})

        # Milestone Check (10, 50, 100 areas)
        total_areas_count = len(all_points)
        if total_areas_count in (10, 50, 100):
            XPEngine.award_xp(
                db, user.id, f"MILESTONE_{total_areas_count}_AREAS", entity_id=f"milestone_{total_areas_count}"
            )
            db.refresh(user)

        message = (xp_res.get("message") if xp_res else None) or "منطقه جدید کشف شد!"
        if poi_xp_res and poi_xp_res.get("xp_earned", 0) > 0 and learned_vibe_name:
            message += f" 📍 مکان '{learned_vibe_name}' کشف شد (+{poi_xp_res['xp_earned']} XP)!"
        elif learned_vibe_name:
            message += f" 🧠 (سلیقه شما بر اساس کشف حوالی '{learned_vibe_name}' آپدیت شد!)"

        progression = XPEngine.calculate_progression(user.score or 0)
        feedback = (xp_res.get("feedback") if xp_res else None) or {
            "badge": "+0 XP",
            "reason": message,
            "level_up": False,
        }

        return {
            "status": xp_res.get("status", "success") if xp_res else "success",
            "message": message,
            "current_points": user.score or 0,
            "all_points": all_points,
            "progression": progression,
            "xp_feedback": feedback,
            "data": {
                "current_points": user.score or 0,
                "all_points": all_points,
            },
            "user_preferences": get_user_preference_vector(user),
        }
    except Exception as exc:
        print(f"Error in discover_fog: {exc}")
        db.rollback()
        return {"message": "خطا در ثبت منطقه", "error": str(exc)}


def get_recommended_pois(db, user_id: int = 1, limit: int = 3):
    repository = ExplorationRepository(db)
    user = repository.get_user_by_id(user_id)

    pois = repository.list_pois(limit=100)
    user_states = db.query(UserPOIState).filter(UserPOIState.user_id == user_id).all()
    state_map = {s.poi_id: s.state for s in user_states}

    scored_pois = []
    for poi in pois:
        st = state_map.get(poi.id, "unknown")
        if st == "hidden":
            continue
        detail = getattr(poi, "details", None)
        if detail and user:
            m_pct = compute_recommendation_score(user, detail)
        else:
            m_pct = 50.0

        payload = build_poi_payload(poi, match_percentage=m_pct, discovery_state=st)
        scored_pois.append((m_pct, payload))

    scored_pois.sort(key=lambda item: item[0], reverse=True)
    return [payload for _, payload in scored_pois[:limit]]


def plan_route(db, lat: float, lon: float, mood: str = "explore"):
    repository = ExplorationRepository(db)
    pois = repository.list_pois(limit=10)

    route_coords = [[lat, lon]]
    for poi in pois[:3]:
        plat, plon = get_poi_lat_lon(poi)
        if plat and plon:
            route_coords.append([plat, plon])

    return {
        "status": "success",
        "message": f"مسیر پیشنهادی با مود '{mood}' ایجاد شد.",
        "route_coordinates": route_coords,
    }
