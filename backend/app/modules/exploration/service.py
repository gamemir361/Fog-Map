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

POI_RARITY_XP = {
    "common": 25,
    "rare": 35,
    "epic": 50,
    "legendary": 100,
}


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

    poi_xp_reward = POI_RARITY_XP.get(rarity, 25)

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
            "xp_reward": poi_xp_reward,
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
            "xp_reward": poi_xp_reward,
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
        "xp_reward": poi_xp_reward,
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

        is_dup = repository.is_duplicate_area(user.id, lat, lon, distance_meters=50.0)
        should_give_points = not is_dup

        # 🎯 Award XP via Central XPEngine & persist ONLY if not duplicate
        xp_res = None
        if should_give_points:
            repository.create_discovered_area(user.id, lat, lon)
            fog_repo.add_fog_discovery(user.id, lat, lon, radius_meters=150.0)
            area_entity_id = f"area_{round(lat, 4)}_{round(lon, 4)}"
            xp_res = XPEngine.award_xp(
                db, user.id, "DISCOVER_AREA", entity_id=area_entity_id, custom_xp=xp_reward
            )
        else:
            progression = XPEngine.calculate_progression(user.score or 0)
            xp_res = {
                "xp_earned": 0,
                "status": "success",
                "message": "مه به آرامی کنار رفت...",
                "is_duplicate": True,
                "progression": progression,
                "feedback": {"badge": "+0 XP", "reason": "منطقه تکراری", "level_up": False},
            }

        # Check POIs within 200m using PostGIS spatial query (Step 3)
        nearby_pois = repository.list_nearby_pois(
            lat, lon, radius_meters=POI_DISCOVERY_CONFIG.get("DISCOVERY_RADIUS_METERS", 200.0)
        )
        learned_vibe_name = ""
        poi_xp_res = None

        initialize_user_poi_states(db, user.id)

        for p in nearby_pois:
            plat, plon = get_poi_lat_lon(p)
            if get_distance_meters(lat, lon, plat, plon) <= POI_DISCOVERY_CONFIG.get("DISCOVERY_RADIUS_METERS", 200.0):
                st_rec = (
                    db.query(UserPOIState)
                    .filter(UserPOIState.user_id == user.id, UserPOIState.poi_id == p.id)
                    .first()
                )
                p_rarity = getattr(p, "rarity", "common") or "common"
                p_xp_val = POI_RARITY_XP.get(p_rarity, 25)
                if not st_rec:
                    st_rec = UserPOIState(
                        user_id=user.id,
                        poi_id=p.id,
                        state="discovered",
                        discovered_at=datetime.datetime.utcnow(),
                        discovery_source="gps",
                    )
                    db.add(st_rec)
                    poi_xp_res = XPEngine.award_xp(
                        db, user.id, "DISCOVER_POI", entity_id=f"poi_{p.id}", custom_xp=p_xp_val
                    )
                elif st_rec.state != "discovered":
                    st_rec.state = "discovered"
                    st_rec.discovered_at = datetime.datetime.utcnow()
                    st_rec.discovery_source = "gps"
                    poi_xp_res = XPEngine.award_xp(
                        db, user.id, "DISCOVER_POI", entity_id=f"poi_{p.id}", custom_xp=p_xp_val
                    )

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

        if not all_points:
            for c in centroids:
                if c.lat is not None and c.lon is not None:
                    key = (round(c.lat, 4), round(c.lon, 4))
                    if key not in all_pts_set:
                        all_pts_set.add(key)
                        all_points.append({"lat": c.lat, "lon": c.lon})

        # Milestone Check (10, 50, 100 areas)
        total_areas_count = len(all_points)

        # Synchronize UserScore.areas_discovered
        user_score_rec = fog_repo.get_or_create_user_score(user.id, user.score or 0)
        if user_score_rec:
            user_score_rec.areas_discovered = total_areas_count
            db.commit()

        if total_areas_count in (10, 50, 100):
            XPEngine.award_xp(
                db, user.id, f"MILESTONE_{total_areas_count}_AREAS", entity_id=f"milestone_{total_areas_count}"
            )
            db.refresh(user)

        # Fast coverage stats for discovery movement ticks (ST_Union skipped for scalability)
        coverage_stats = fog_repo.get_user_coverage_stats(user.id, compute_union=False)

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
            "coverage_stats": coverage_stats,
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


def get_nearby_events(
    db,
    lat: float,
    lon: float,
    radius: Optional[float] = 10000.0,
    status_filter: Optional[str] = "active",
    event_type: Optional[str] = None,
    sort_by: Optional[str] = "distance",
    limit: int = 50,
    current_user_id: Optional[int] = None,
):
    if lat < -90.0 or lat > 90.0:
        raise ValueError("عرض جغرافیایی (latitude) نامعتبر است.")
    if lon < -180.0 or lon > 180.0:
        raise ValueError("طول جغرافیایی (longitude) نامعتبر است.")

    norm_type = event_type.lower().strip() if event_type else None
    if norm_type and norm_type not in {"all", "cultural", "historical", "challenge", "nature", "exploration"}:
        raise ValueError("نوع رویداد نامعتبر است.")

    norm_status = status_filter.lower().strip() if status_filter else None
    if norm_status and norm_status not in {"all", "active", "scheduled", "ended", "ending_soon"}:
        raise ValueError("وضعیت رویداد نامعتبر است.")

    norm_sort = sort_by.lower().strip() if sort_by else "distance"
    if norm_sort and norm_sort not in {"distance", "xp", "ending_soon"}:
        raise ValueError("نحوه مرتب‌سازی نامعتبر است.")

    safe_radius = max(1.0, min(float(radius or 10000.0), 100000.0))
    safe_limit = max(1, min(int(limit or 50), 100))
    now = datetime.datetime.utcnow()

    from sqlalchemy import text
    from app.modules.exploration.models import ExplorationEvent, ExplorationEventParticipation

    participated_event_ids = set()
    if current_user_id:
        try:
            participated_event_ids = set(
                r[0]
                for r in db.query(ExplorationEventParticipation.event_id)
                .filter(ExplorationEventParticipation.user_id == current_user_id)
                .all()
            )
        except Exception:
            pass

    events_result = []

    try:
        status_clause = ""
        type_clause = ""
        params = {
            "lat": lat,
            "lon": lon,
            "radius": safe_radius,
            "now": now,
            "soon_threshold": now + datetime.timedelta(hours=4),
            "limit": safe_limit,
        }

        if norm_status == "active":
            status_clause = "AND starts_at <= :now AND ends_at > :now"
        elif norm_status == "scheduled":
            status_clause = "AND starts_at > :now"
        elif norm_status == "ended":
            status_clause = "AND ends_at <= :now"
        elif norm_status == "ending_soon":
            status_clause = "AND starts_at <= :now AND ends_at > :now AND ends_at <= :soon_threshold"

        if norm_type and norm_type != "all":
            type_clause = "AND event_type = :event_type"
            params["event_type"] = norm_type

        order_clause = "ORDER BY dist_m ASC, id ASC"
        if norm_sort == "xp":
            order_clause = "ORDER BY xp_reward DESC, dist_m ASC, id ASC"
        elif norm_sort == "ending_soon":
            order_clause = "ORDER BY ends_at ASC, dist_m ASC, id ASC"

        raw_sql = text(f"""
            SELECT 
                id,
                title,
                description,
                event_type,
                status,
                latitude,
                longitude,
                radius_meters,
                xp_reward,
                starts_at,
                ends_at,
                is_active,
                ST_Distance(
                    geometry::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) as dist_m
            FROM exploration_events
            WHERE is_active IS TRUE
              {status_clause}
              {type_clause}
              AND ST_DWithin(
                  geometry::geography,
                  ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                  :radius
              )
            {order_clause}
            LIMIT :limit
        """)

        rows = db.execute(raw_sql, params).fetchall()

        for r in rows:
            dist_val = round(float(r.dist_m), 1)
            e_starts = r.starts_at.isoformat() if isinstance(r.starts_at, datetime.datetime) else str(r.starts_at)
            e_ends = r.ends_at.isoformat() if isinstance(r.ends_at, datetime.datetime) else str(r.ends_at)

            if r.starts_at and now < r.starts_at:
                dyn_status = "scheduled"
            elif r.ends_at and now >= r.ends_at:
                dyn_status = "ended"
            else:
                dyn_status = "active"

            rem_seconds = 0
            if r.ends_at and now < r.ends_at:
                rem_seconds = int((r.ends_at - now).total_seconds())

            is_ending_soon = (dyn_status == "active" and 0 < rem_seconds <= 14400)
            fmt_time = None
            if dyn_status == "active" and rem_seconds > 0:
                h = rem_seconds // 3600
                m = (rem_seconds % 3600) // 60
                fmt_time = f"{h} ساعت و {m} دقیقه باقی مانده" if h > 0 else f"{m} دقیقه باقی مانده"

            events_result.append(
                {
                    "id": r.id,
                    "title": r.title,
                    "description": r.description,
                    "event_type": r.event_type,
                    "status": dyn_status,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "radius_meters": r.radius_meters,
                    "distance_meters": dist_val,
                    "inside_geofence": dist_val <= r.radius_meters,
                    "already_participated": (r.id in participated_event_ids),
                    "xp_reward": r.xp_reward,
                    "starts_at": e_starts,
                    "ends_at": e_ends,
                    "is_active": r.is_active,
                    "remaining_seconds": rem_seconds,
                    "formatted_remaining_time": fmt_time,
                    "is_ending_soon": is_ending_soon,
                }
            )

        return events_result

    except Exception:
        query = db.query(ExplorationEvent).filter(ExplorationEvent.is_active.is_(True))
        if norm_type and norm_type != "all":
            query = query.filter(ExplorationEvent.event_type == norm_type)

        all_events = query.all()
        candidates = []

        for e in all_events:
            if e.starts_at and now < e.starts_at:
                dyn_status = "scheduled"
            elif e.ends_at and now >= e.ends_at:
                dyn_status = "ended"
            else:
                dyn_status = "active"

            rem_seconds = 0
            if e.ends_at and now < e.ends_at:
                rem_seconds = int((e.ends_at - now).total_seconds())

            is_ending_soon = (dyn_status == "active" and 0 < rem_seconds <= 14400)

            if norm_status and norm_status != "all":
                if norm_status == "ending_soon":
                    if not is_ending_soon:
                        continue
                elif dyn_status != norm_status:
                    continue

            d_lat = (e.latitude - lat) * 111320.0
            d_lon = (e.longitude - lon) * 111320.0 * math.cos(math.radians(lat))
            dist = math.sqrt(d_lat * d_lat + d_lon * d_lon)

            if dist <= safe_radius:
                dist_val = round(dist, 1)
                e_starts = e.starts_at.isoformat() if isinstance(e.starts_at, datetime.datetime) else str(e.starts_at)
                e_ends = e.ends_at.isoformat() if isinstance(e.ends_at, datetime.datetime) else str(e.ends_at)
                fmt_time = None
                if dyn_status == "active" and rem_seconds > 0:
                    h = rem_seconds // 3600
                    m = (rem_seconds % 3600) // 60
                    fmt_time = f"{h} ساعت و {m} دقیقه باقی مانده" if h > 0 else f"{m} دقیقه باقی مانده"

                candidates.append(
                    {
                        "id": e.id,
                        "title": e.title,
                        "description": e.description,
                        "event_type": e.event_type,
                        "status": dyn_status,
                        "latitude": e.latitude,
                        "longitude": e.longitude,
                        "radius_meters": e.radius_meters,
                        "distance_meters": dist_val,
                        "inside_geofence": dist_val <= e.radius_meters,
                        "already_participated": (e.id in participated_event_ids),
                        "xp_reward": e.xp_reward,
                        "starts_at": e_starts,
                        "ends_at": e_ends,
                        "is_active": e.is_active,
                        "remaining_seconds": rem_seconds,
                        "formatted_remaining_time": fmt_time,
                        "is_ending_soon": is_ending_soon,
                    }
                )

        if norm_sort == "xp":
            candidates.sort(key=lambda x: (-x["xp_reward"], x["distance_meters"], x["id"]))
        elif norm_sort == "ending_soon":
            candidates.sort(key=lambda x: (x["remaining_seconds"] if x["remaining_seconds"] > 0 else 99999999, x["distance_meters"], x["id"]))
        else:
            candidates.sort(key=lambda x: (x["distance_meters"], x["id"]))

        return candidates[:safe_limit]


def participate_event(db, user_id: int, event_id: int, lat: float, lon: float):
    if lat < -90.0 or lat > 90.0:
        raise ValueError("عرض جغرافیایی (latitude) نامعتبر است.")
    if lon < -180.0 or lon > 180.0:
        raise ValueError("طول جغرافیایی (longitude) نامعتبر است.")

    from fastapi import HTTPException
    from sqlalchemy.exc import IntegrityError
    from app.modules.exploration.models import ExplorationEvent, ExplorationEventParticipation
    from app.modules.gamification.xp_engine import XPEngine

    event = db.query(ExplorationEvent).filter(ExplorationEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="رویداد مورد نظر یافت نشد.")

    now = datetime.datetime.utcnow()

    if not event.is_active or (event.starts_at and now < event.starts_at) or (event.ends_at and now >= event.ends_at):
        raise HTTPException(status_code=400, detail="این رویداد در حال حاضر فعال نیست.")

    # Calculate actual geographic distance
    dist_m = None
    try:
        from sqlalchemy import text
        raw_sql = text("""
            SELECT ST_Distance(
                geometry::geography,
                ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
            ) as dist_m
            FROM exploration_events
            WHERE id = :event_id
        """)
        row = db.execute(raw_sql, {"lon": lon, "lat": lat, "event_id": event_id}).fetchone()
        if row and row.dist_m is not None:
            dist_m = float(row.dist_m)
    except Exception:
        pass

    if dist_m is None:
        d_lat = (event.latitude - lat) * 111320.0
        d_lon = (event.longitude - lon) * 111320.0 * math.cos(math.radians(lat))
        dist_m = math.sqrt(d_lat * d_lat + d_lon * d_lon)

    dist_val = round(dist_m, 1)

    if dist_val > event.radius_meters:
        raise HTTPException(
            status_code=400,
            detail=f"برای شرکت در این رویداد باید وارد محدوده شوید. (فاصله فعلی: {dist_val} متر، شعاع رویداد: {event.radius_meters} متر)"
        )

    # Check existing participation (Anti-Farming)
    existing = (
        db.query(ExplorationEventParticipation)
        .filter(
            ExplorationEventParticipation.user_id == user_id,
            ExplorationEventParticipation.event_id == event_id,
        )
        .first()
    )
    if existing:
        progression = XPEngine.calculate_progression(XPEngine.get_user_xp(db, user_id))
        return {
            "status": "success",
            "message": f"شما قبلاً در رویداد '{event.title}' شرکت کرده‌اید.",
            "event_id": event.id,
            "event_title": event.title,
            "distance_meters": dist_val,
            "xp_earned": 0,
            "already_participated": True,
            "progression": progression,
        }

    try:
        participation = ExplorationEventParticipation(
            event_id=event.id,
            user_id=user_id,
            latitude=lat,
            longitude=lon,
            distance_meters=dist_val,
            xp_awarded=event.xp_reward,
        )
        db.add(participation)
        db.flush()

        xp_res = XPEngine.award_xp(
            db,
            user_id=user_id,
            event_type="EVENT_PARTICIPATION",
            entity_id=f"event_{event.id}",
            reason=f"شرکت در رویداد '{event.title}'",
            custom_xp=event.xp_reward,
        )

        # Create activity log entry for user participation
        from app.modules.exploration.models import ExplorationEventActivity
        user_obj = db.query(User).filter(User.id == user_id).first()
        username_val = user_obj.username if user_obj and user_obj.username else f"explorer_{user_id}"
        act_part = ExplorationEventActivity(
            event_id=event.id,
            user_id=user_id,
            activity_type="participation",
            title=f"مشارکت {username_val}",
            description=f"{username_val} در رویداد '{event.title}' شرکت کرد",
            xp_earned=event.xp_reward,
            created_at=datetime.datetime.utcnow(),
        )
        db.add(act_part)
        db.flush()

        # Check community challenge completion
        from sqlalchemy import func
        stats = (
            db.query(
                func.count(ExplorationEventParticipation.id).label("total_participants"),
                func.coalesce(func.sum(ExplorationEventParticipation.xp_awarded), 0).label("total_xp"),
            )
            .filter(ExplorationEventParticipation.event_id == event.id)
            .first()
        )
        part_count = int(stats.total_participants or 0)
        tot_xp = int(stats.total_xp or 0)

        target_part = getattr(event, "target_participants", None) or 50
        target_xp = getattr(event, "target_xp", None) or (target_part * event.xp_reward)

        if part_count >= target_part or tot_xp >= target_xp:
            existing_comp = (
                db.query(ExplorationEventActivity)
                .filter(
                    ExplorationEventActivity.event_id == event.id,
                    ExplorationEventActivity.activity_type == "challenge_completed",
                )
                .first()
            )
            if not existing_comp:
                act_comp = ExplorationEventActivity(
                    event_id=event.id,
                    user_id=None,
                    activity_type="challenge_completed",
                    title="تکمیل چالش جامعه",
                    description=f"🎉 چالش جامعه برای رویداد '{event.title}' با موفقیت تکمیل شد!",
                    xp_earned=getattr(event, "community_reward_xp", 500) or 500,
                    progress_pct=100.0,
                    created_at=datetime.datetime.utcnow(),
                )
                db.add(act_comp)
                db.flush()

        db.commit()

        return {
            "status": "success",
            "message": f"🎉 رویداد '{event.title}' با موفقیت تکمیل شد! +{event.xp_reward} XP کسب کردید.",
            "event_id": event.id,
            "event_title": event.title,
            "distance_meters": dist_val,
            "xp_earned": xp_res.get("xp_earned", event.xp_reward),
            "already_participated": False,
            "progression": xp_res.get("progression"),
        }
    except IntegrityError:
        db.rollback()
        progression = XPEngine.calculate_progression(XPEngine.get_user_xp(db, user_id))
        return {
            "status": "success",
            "message": f"شما قبلاً در رویداد '{event.title}' شرکت کرده‌اید.",
            "event_id": event.id,
            "event_title": event.title,
            "distance_meters": dist_val,
            "xp_earned": 0,
            "already_participated": True,
            "progression": progression,
        }


def get_event_density(
    db,
    min_lat: float,
    min_lon: float,
    max_lat: float,
    max_lon: float,
    zoom: int = 13,
    event_type: Optional[str] = None,
    status_filter: Optional[str] = "active",
):
    if min_lat < -90.0 or max_lat > 90.0 or min_lat > max_lat:
        raise ValueError("بازه عرض جغرافیایی (latitude) نامعتبر است.")
    if min_lon < -180.0 or max_lon > 180.0 or min_lon > max_lon:
        raise ValueError("بازه طول جغرافیایی (longitude) نامعتبر است.")

    norm_type = event_type.lower().strip() if event_type else None
    if norm_type and norm_type not in {"all", "cultural", "historical", "challenge", "nature", "exploration"}:
        raise ValueError("نوع رویداد نامعتبر است.")

    norm_status = status_filter.lower().strip() if status_filter else None
    if norm_status and norm_status not in {"all", "active", "scheduled", "ended", "ending_soon"}:
        raise ValueError("وضعیت رویداد نامعتبر است.")

    safe_zoom = max(1, min(int(zoom or 13), 20))
    now = datetime.datetime.utcnow()

    # Zoom-dependent grid snap size (degrees)
    grid_size = max(0.0005, min(0.5, 360.0 / (2.0 ** (safe_zoom + 2))))

    from sqlalchemy import text
    from app.modules.exploration.models import ExplorationEvent

    clusters = []

    try:
        status_clause = ""
        params = {
            "min_lat": min_lat,
            "max_lat": max_lat,
            "min_lon": min_lon,
            "max_lon": max_lon,
            "grid_size": grid_size,
            "now": now,
            "soon_threshold": now + datetime.timedelta(hours=4),
        }

        if norm_status == "active":
            status_clause = "AND starts_at <= :now AND ends_at > :now"
        elif norm_status == "scheduled":
            status_clause = "AND starts_at > :now"
        elif norm_status == "ended":
            status_clause = "AND ends_at <= :now"
        elif norm_status == "ending_soon":
            status_clause = "AND starts_at <= :now AND ends_at > :now AND ends_at <= :soon_threshold"

        type_clause = ""
        if norm_type and norm_type != "all":
            type_clause = "AND event_type = :event_type"
            params["event_type"] = norm_type

        raw_sql = text(f"""
            SELECT 
                AVG(latitude) as lat,
                AVG(longitude) as lon,
                COUNT(id) as total_count,
                COUNT(CASE WHEN event_type = 'cultural' THEN 1 END) as c_cultural,
                COUNT(CASE WHEN event_type = 'historical' THEN 1 END) as c_historical,
                COUNT(CASE WHEN event_type = 'challenge' THEN 1 END) as c_challenge,
                COUNT(CASE WHEN event_type = 'nature' THEN 1 END) as c_nature,
                COUNT(CASE WHEN event_type = 'exploration' THEN 1 END) as c_exploration
            FROM exploration_events
            WHERE is_active IS TRUE
              {status_clause}
              {type_clause}
              AND latitude BETWEEN :min_lat AND :max_lat
              AND longitude BETWEEN :min_lon AND :max_lon
            GROUP BY ST_SnapToGrid(geometry, :grid_size)
            ORDER BY total_count DESC
            LIMIT 50
        """)

        rows = db.execute(raw_sql, params).fetchall()

        for r in rows:
            types_dict = {}
            if r.c_cultural > 0: types_dict["cultural"] = int(r.c_cultural)
            if r.c_historical > 0: types_dict["historical"] = int(r.c_historical)
            if r.c_challenge > 0: types_dict["challenge"] = int(r.c_challenge)
            if r.c_nature > 0: types_dict["nature"] = int(r.c_nature)
            if r.c_exploration > 0: types_dict["exploration"] = int(r.c_exploration)

            clusters.append(
                {
                    "latitude": round(float(r.lat), 5),
                    "longitude": round(float(r.lon), 5),
                    "event_count": int(r.total_count),
                    "event_types": types_dict,
                }
            )

        return clusters

    except Exception:
        # Fallback for SQLite / non-PostGIS test environment
        query = db.query(ExplorationEvent).filter(
            ExplorationEvent.is_active.is_(True),
            ExplorationEvent.latitude.between(min_lat, max_lat),
            ExplorationEvent.longitude.between(min_lon, max_lon),
        )

        all_events = query.all()
        grid_buckets = {}

        for e in all_events:
            if e.starts_at and now < e.starts_at:
                dyn_status = "scheduled"
            elif e.ends_at and now >= e.ends_at:
                dyn_status = "ended"
            else:
                dyn_status = "active"

            if status_filter and status_filter != "all" and dyn_status != status_filter:
                continue

            if event_type and event_type.lower() != "all" and e.event_type != event_type.lower():
                continue

            gx = math.floor(e.longitude / grid_size)
            gy = math.floor(e.latitude / grid_size)
            key = (gx, gy)

            if key not in grid_buckets:
                grid_buckets[key] = []
            grid_buckets[key].append(e)

        for _, evts in grid_buckets.items():
            avg_lat = sum(e.latitude for e in evts) / len(evts)
            avg_lon = sum(e.longitude for e in evts) / len(evts)
            types_dict = {}
            for e in evts:
                types_dict[e.event_type] = types_dict.get(e.event_type, 0) + 1

            clusters.append(
                {
                    "latitude": round(avg_lat, 5),
                    "longitude": round(avg_lon, 5),
                    "event_count": len(evts),
                    "event_types": types_dict,
                }
            )

        clusters.sort(key=lambda c: c["event_count"], reverse=True)
        return clusters[:50]


def get_event_leaderboard(
    db,
    event_id: int,
    limit: int = 10,
    current_user_id: Optional[int] = None,
):
    from fastapi import HTTPException
    from sqlalchemy import func
    from app.modules.exploration.models import ExplorationEvent, ExplorationEventParticipation
    from app.modules.users.models import User

    event = db.query(ExplorationEvent).filter(ExplorationEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="رویداد مورد نظر یافت نشد.")

    safe_limit = max(1, min(int(limit or 10), 50))
    now = datetime.datetime.utcnow()

    # 1. Total participant count & total XP earned in event
    stats = (
        db.query(
            func.count(ExplorationEventParticipation.id).label("total_participants"),
            func.coalesce(func.sum(ExplorationEventParticipation.xp_awarded), 0).label("total_xp"),
        )
        .filter(ExplorationEventParticipation.event_id == event_id)
        .first()
    )
    participant_count = int(stats.total_participants or 0)
    total_xp_earned = int(stats.total_xp or 0)

    # 2. Fetch Top N leaderboard entries (Ordered by score DESC, participated_at ASC, user_id ASC)
    top_entries_query = (
        db.query(
            ExplorationEventParticipation.user_id,
            ExplorationEventParticipation.xp_awarded,
            ExplorationEventParticipation.participated_at,
            User.username,
        )
        .outerjoin(User, ExplorationEventParticipation.user_id == User.id)
        .filter(ExplorationEventParticipation.event_id == event_id)
        .order_by(
            ExplorationEventParticipation.xp_awarded.desc(),
            ExplorationEventParticipation.participated_at.asc(),
            ExplorationEventParticipation.user_id.asc(),
        )
        .limit(safe_limit)
        .all()
    )

    entries = []
    for rank_idx, r in enumerate(top_entries_query, start=1):
        display_name = r.username if r.username else f"explorer_{r.user_id}"
        entries.append(
            {
                "rank": rank_idx,
                "user_id": r.user_id,
                "display_name": display_name,
                "score": int(r.xp_awarded or 0),
            }
        )

    # 3. Compute Current User Rank (even if outside Top N)
    current_user_rank_obj = None
    if current_user_id:
        user_part = (
            db.query(ExplorationEventParticipation)
            .filter(
                ExplorationEventParticipation.event_id == event_id,
                ExplorationEventParticipation.user_id == current_user_id,
            )
            .first()
        )
        if user_part:
            higher_count = (
                db.query(ExplorationEventParticipation)
                .filter(
                    ExplorationEventParticipation.event_id == event_id,
                    (
                        (ExplorationEventParticipation.xp_awarded > user_part.xp_awarded)
                        | (
                            (ExplorationEventParticipation.xp_awarded == user_part.xp_awarded)
                            & (ExplorationEventParticipation.participated_at < user_part.participated_at)
                        )
                        | (
                            (ExplorationEventParticipation.xp_awarded == user_part.xp_awarded)
                            & (ExplorationEventParticipation.participated_at == user_part.participated_at)
                            & (ExplorationEventParticipation.user_id < user_part.user_id)
                        )
                    ),
                )
                .count()
            )
            user_rank = higher_count + 1
            current_user_rank_obj = {
                "has_participated": True,
                "rank": user_rank,
                "score": int(user_part.xp_awarded or 0),
                "user_id": current_user_id,
            }
        else:
            current_user_rank_obj = {
                "has_participated": False,
                "rank": None,
                "score": None,
                "user_id": current_user_id,
            }

    # 4. Community Challenge Status & Progress
    target_participants = getattr(event, "target_participants", None) or 50
    target_xp = getattr(event, "target_xp", None) or (target_participants * event.xp_reward)
    community_reward_xp = getattr(event, "community_reward_xp", None) or 500

    part_pct = round(min(100.0, (participant_count / max(1, target_participants)) * 100.0), 1)
    xp_pct = round(min(100.0, (total_xp_earned / max(1, target_xp)) * 100.0), 1)

    if event.starts_at and now < event.starts_at:
        challenge_status = "upcoming"
    elif participant_count >= target_participants or total_xp_earned >= target_xp:
        challenge_status = "completed"
    elif event.ends_at and now >= event.ends_at:
        challenge_status = "expired"
    else:
        challenge_status = "active"

    challenge_obj = {
        "enabled": True,
        "status": challenge_status,
        "target_participants": target_participants,
        "current_participants": participant_count,
        "participants_progress_pct": part_pct,
        "target_xp": target_xp,
        "current_xp": total_xp_earned,
        "xp_progress_pct": xp_pct,
        "community_reward_xp": community_reward_xp,
    }

    return {
        "status": "success",
        "event_id": event.id,
        "event_title": event.title,
        "participant_count": participant_count,
        "total_xp_earned": total_xp_earned,
        "entries": entries,
        "current_user": current_user_rank_obj,
        "challenge": challenge_obj,
    }


def get_event_activities(
    db,
    event_id: Optional[int] = None,
    limit: int = 20,
    cursor_id: Optional[int] = None,
):
    from app.modules.exploration.models import ExplorationEvent, ExplorationEventActivity
    from app.modules.users.models import User

    safe_limit = max(1, min(int(limit or 20), 50))

    query = (
        db.query(
            ExplorationEventActivity,
            ExplorationEvent.title.label("event_title"),
            User.username,
        )
        .join(ExplorationEvent, ExplorationEventActivity.event_id == ExplorationEvent.id)
        .outerjoin(User, ExplorationEventActivity.user_id == User.id)
    )

    if event_id:
        query = query.filter(ExplorationEventActivity.event_id == event_id)

    if cursor_id:
        query = query.filter(ExplorationEventActivity.id < cursor_id)

    query = query.order_by(ExplorationEventActivity.id.desc()).limit(safe_limit)
    rows = query.all()

    activities = []
    for act, event_title, username in rows:
        display_name = username if username else (f"explorer_{act.user_id}" if act.user_id else None)
        c_at = act.created_at.isoformat() if isinstance(act.created_at, datetime.datetime) else str(act.created_at)

        activities.append(
            {
                "id": act.id,
                "event_id": act.event_id,
                "event_title": event_title,
                "user_id": act.user_id,
                "display_name": display_name,
                "activity_type": act.activity_type,
                "title": act.title,
                "description": act.description,
                "xp_earned": act.xp_earned,
                "progress_pct": act.progress_pct,
                "created_at": c_at,
            }
        )

    return activities


def get_event_by_id(
    db,
    event_id: int,
    current_user_id: Optional[int] = None,
    user_lat: Optional[float] = None,
    user_lon: Optional[float] = None,
):
    from fastapi import HTTPException
    from app.modules.exploration.models import ExplorationEvent, ExplorationEventParticipation

    event = db.query(ExplorationEvent).filter(ExplorationEvent.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="رویداد مورد نظر یافت نشد.")

    now = datetime.datetime.utcnow()

    if event.starts_at and now < event.starts_at:
        dyn_status = "scheduled"
    elif event.ends_at and now >= event.ends_at:
        dyn_status = "ended"
    else:
        dyn_status = "active"

    rem_seconds = 0
    if event.ends_at and now < event.ends_at:
        rem_seconds = int((event.ends_at - now).total_seconds())

    is_ending_soon = (dyn_status == "active" and 0 < rem_seconds <= 14400)
    fmt_time = None
    if dyn_status == "active" and rem_seconds > 0:
        h = rem_seconds // 3600
        m = (rem_seconds % 3600) // 60
        fmt_time = f"{h} ساعت و {m} دقیقه باقی مانده" if h > 0 else f"{m} دقیقه باقی مانده"

    dist_val = 0.0
    inside = False
    if user_lat is not None and user_lon is not None:
        try:
            from sqlalchemy import text
            raw_sql = text("""
                SELECT ST_Distance(
                    geometry::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography
                ) as dist_m
                FROM exploration_events
                WHERE id = :event_id
            """)
            row = db.execute(raw_sql, {"lon": user_lon, "lat": user_lat, "event_id": event_id}).fetchone()
            if row and row.dist_m is not None:
                dist_val = round(float(row.dist_m), 1)
        except Exception:
            d_lat = (event.latitude - user_lat) * 111320.0
            d_lon = (event.longitude - user_lon) * 111320.0 * math.cos(math.radians(user_lat))
            dist_val = round(math.sqrt(d_lat * d_lat + d_lon * d_lon), 1)

        inside = dist_val <= event.radius_meters

    already_part = False
    if current_user_id:
        try:
            already_part = (
                db.query(ExplorationEventParticipation)
                .filter(
                    ExplorationEventParticipation.user_id == current_user_id,
                    ExplorationEventParticipation.event_id == event_id,
                )
                .first()
                is not None
            )
        except Exception:
            pass

    e_starts = event.starts_at.isoformat() if isinstance(event.starts_at, datetime.datetime) else str(event.starts_at)
    e_ends = event.ends_at.isoformat() if isinstance(event.ends_at, datetime.datetime) else str(event.ends_at)

    return {
        "id": event.id,
        "title": event.title,
        "description": event.description,
        "event_type": event.event_type,
        "status": dyn_status,
        "latitude": event.latitude,
        "longitude": event.longitude,
        "radius_meters": event.radius_meters,
        "distance_meters": dist_val,
        "inside_geofence": inside,
        "already_participated": already_part,
        "xp_reward": event.xp_reward,
        "starts_at": e_starts,
        "ends_at": e_ends,
        "is_active": event.is_active,
        "remaining_seconds": rem_seconds,
        "formatted_remaining_time": fmt_time,
        "is_ending_soon": is_ending_soon,
    }
