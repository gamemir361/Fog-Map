from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_current_user
from app.modules.users.models import User
from app.modules.exploration.schemas import (
    FogDiscoverRequest,
    FogDiscoverResponse,
    POIResponse,
    RoutePlanRequest,
    RoutePlanResponse,
    ExplorationEventResponse,
    NearbyEventsResponse,
    SingleEventResponse,
    EventParticipateRequest,
    EventParticipateResponse,
    EventDensityResponse,
    EventLeaderboardResponse,
    EventActivityFeedResponse,
)
from app.modules.exploration.service import (
    discover_fog,
    get_recommended_pois,
    list_pois,
    plan_route,
    get_nearby_events,
    get_event_by_id,
    participate_event,
    get_event_density,
    get_event_leaderboard,
    get_event_activities,
)

router = APIRouter()


@router.get("/events/activity", response_model=EventActivityFeedResponse)
def get_event_activity_feed_endpoint(
    event_id: Optional[int] = Query(None, description="Filter activity by event_id"),
    limit: Optional[int] = Query(20, ge=1, le=50, description="Max activities to return"),
    cursor_id: Optional[int] = Query(None, description="Cursor for pagination (older than id)"),
    db: Session = Depends(get_db),
):
    try:
        activities = get_event_activities(
            db=db,
            event_id=event_id,
            limit=limit or 20,
            cursor_id=cursor_id,
        )
        return {
            "status": "success",
            "count": len(activities),
            "activities": activities,
        }
    except ValueError as val_err:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(val_err))


@router.get("/events/{event_id}/leaderboard", response_model=EventLeaderboardResponse)
def get_event_leaderboard_endpoint(
    event_id: int,
    limit: Optional[int] = Query(10, ge=1, le=50, description="Number of top entries to return"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    return get_event_leaderboard(
        db=db,
        event_id=event_id,
        limit=limit or 10,
        current_user_id=user_id,
    )


@router.get("/events/density", response_model=EventDensityResponse)
def get_event_density_endpoint(
    min_lat: float = Query(..., description="Minimum Latitude"),
    min_lon: float = Query(..., description="Minimum Longitude"),
    max_lat: float = Query(..., description="Maximum Latitude"),
    max_lon: float = Query(..., description="Maximum Longitude"),
    zoom: Optional[int] = Query(13, ge=1, le=22, description="Map zoom level"),
    event_type: Optional[str] = Query(None, description="Event type filter"),
    status: Optional[str] = Query("active", description="Status filter: active, scheduled, ended, all"),
    db: Session = Depends(get_db),
):
    try:
        clusters = get_event_density(
            db=db,
            min_lat=min_lat,
            min_lon=min_lon,
            max_lat=max_lat,
            max_lon=max_lon,
            zoom=zoom or 13,
            event_type=event_type,
            status_filter=status,
        )
        return {
            "status": "success",
            "zoom": zoom or 13,
            "count": len(clusters),
            "clusters": clusters,
        }
    except ValueError as val_err:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(val_err))


@router.get("/events/nearby", response_model=NearbyEventsResponse)
def get_nearby_events_endpoint(
    lat: float = Query(..., description="عرض جغرافیایی (Latitude)"),
    lon: float = Query(..., description="طول جغرافیایی (Longitude)"),
    radius: Optional[float] = Query(10000.0, description="شعاع جستجو به متر"),
    status: Optional[str] = Query("active", description="فیلتر وضعیت: active, scheduled, ended, ending_soon, all"),
    event_type: Optional[str] = Query(None, description="فیلتر نوع رویداد: cultural, historical, challenge, nature, exploration, all"),
    sort: Optional[str] = Query("distance", description="مرتب‌سازی: distance, xp, ending_soon"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="حداکثر تعداد نتایج"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    try:
        user_id = current_user.id if current_user else None
        events = get_nearby_events(
            db=db,
            lat=lat,
            lon=lon,
            radius=radius,
            status_filter=status,
            event_type=event_type,
            sort_by=sort,
            limit=limit or 50,
            current_user_id=user_id,
        )
        return {
            "status": "success",
            "message": f"تعداد {len(events)} رویداد در محدوده یافت شد.",
            "count": len(events),
            "events": events,
        }
    except ValueError as val_err:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(val_err))
    except HTTPException:
        raise
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"خطا در دریافت رویدادها: {str(exc)}")


@router.get("/events/{event_id}", response_model=SingleEventResponse)
def get_event_detail_endpoint(
    event_id: int,
    lat: Optional[float] = Query(None, description="Player latitude"),
    lon: Optional[float] = Query(None, description="Player longitude"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    user_id = current_user.id if current_user else None
    evt_dict = get_event_by_id(
        db=db,
        event_id=event_id,
        current_user_id=user_id,
        user_lat=lat,
        user_lon=lon,
    )
    return {
        "status": "success",
        "event": evt_dict,
    }


@router.post("/events/{event_id}/participate", response_model=EventParticipateResponse)
def participate_in_event(
    event_id: int,
    req: EventParticipateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        res = participate_event(
            db=db,
            user_id=current_user.id,
            event_id=event_id,
            lat=req.latitude,
            lon=req.longitude,
        )
        return res
    except ValueError as val_err:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(val_err))


@router.get("/pois", response_model=list[POIResponse])
def get_pois(
    category: Optional[str] = Query(None, description="Filter by category (nature, culture, energy, quiet, photography, nightlife)"),
    search: Optional[str] = Query(None, description="Fuzzy search by name or description"),
    bbox: Optional[str] = Query(None, description="Bounding Box: min_lon,min_lat,max_lon,max_lat"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    target_user_id = current_user.id if current_user else user_id
    return list_pois(db, category=category, search=search, bbox=bbox, limit=limit, offset=offset, user_id=target_user_id)


@router.post("/pois/{poi_id}/discover")
def discover_poi(
    poi_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    user_id: int = 1,
):
    import datetime
    from app.modules.exploration.models import POI, UserPOIDiscovery, UserPOIState
    from app.modules.exploration.service import build_poi_payload
    from app.modules.gamification.xp_engine import XPEngine
    from app.modules.missions.service import update_user_missions

    target_user_id = current_user.id if current_user else user_id
    poi = db.query(POI).filter(POI.id == poi_id).first()
    if not poi:
        return {"status": "error", "message": "مكان يافت نشد."}

    st_rec = (
        db.query(UserPOIState)
        .filter(UserPOIState.user_id == target_user_id, UserPOIState.poi_id == poi_id)
        .first()
    )

    prev_state = st_rec.state if st_rec else "unknown"
    if not st_rec:
        st_rec = UserPOIState(
            user_id=target_user_id,
            poi_id=poi_id,
            state="discovered",
            discovered_at=datetime.datetime.utcnow(),
            discovery_source="manual",
        )
        db.add(st_rec)
    elif st_rec.state != "discovered":
        st_rec.state = "discovered"
        st_rec.discovered_at = datetime.datetime.utcnow()
        st_rec.discovery_source = "manual"

    existing_disc = (
        db.query(UserPOIDiscovery)
        .filter(UserPOIDiscovery.user_id == target_user_id, UserPOIDiscovery.poi_id == poi_id)
        .first()
    )
    if not existing_disc:
        db.add(UserPOIDiscovery(user_id=target_user_id, poi_id=poi_id))

    db.commit()

    from app.modules.exploration.service import POI_RARITY_XP
    p_rarity = getattr(poi, "rarity", "common") or "common"
    p_xp = POI_RARITY_XP.get(p_rarity, 25)
    xp_res = XPEngine.award_xp(db, target_user_id, "DISCOVER_POI", entity_id=f"poi_{poi_id}", custom_xp=p_xp)
    update_user_missions(db, target_user_id, "visit_poi", {"category": poi.category})

    payload = build_poi_payload(
        poi,
        discovery_state="discovered",
        discovered_at=st_rec.discovered_at,
        discovery_source=st_rec.discovery_source,
    )
    payload["xp_feedback"] = xp_res.get("feedback")
    payload["xp_earned"] = xp_res.get("xp_earned", 0)
    payload["just_discovered"] = (prev_state != "discovered")

    return payload


@router.post("/fog/discover", response_model=FogDiscoverResponse)
def discover(
    req: FogDiscoverRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    target_user_id = current_user.id if current_user else (req.user_id or 1)
    return discover_fog(db, target_user_id, req.lat, req.lon)


@router.get("/pois/recommended", response_model=list[POIResponse])
def get_recommended(
    user_id: int = 1,
    limit: int = Query(3, ge=1, le=10),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    target_user_id = current_user.id if current_user else user_id
    return get_recommended_pois(db, user_id=target_user_id, limit=limit)


@router.post("/routes/plan", response_model=RoutePlanResponse)
def plan(req: RoutePlanRequest, db: Session = Depends(get_db)):
    return plan_route(db, req.lat, req.lon, req.mood)


@router.post("/routes/complete")
def complete_route(
    route_id: str = Query(..., description="Route ID or Identifier"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    user_id: int = 1,
):
    from app.modules.gamification.xp_engine import XPEngine
    target_user_id = current_user.id if current_user else user_id
    res = XPEngine.award_xp(
        db, target_user_id, "COMPLETE_ROUTE", entity_id=f"route_{route_id}", reason=f"اتمام مسیر {route_id}"
    )
    return res
