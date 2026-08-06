from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_current_user
from app.modules.users.models import User
from app.modules.exploration.schemas import (
    FogDiscoverRequest,
    FogDiscoverResponse,
    POIResponse,
    RoutePlanRequest,
    RoutePlanResponse,
)
from app.modules.exploration.service import (
    discover_fog,
    get_recommended_pois,
    list_pois,
    plan_route,
)

router = APIRouter()


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

    xp_res = XPEngine.award_xp(db, target_user_id, "DISCOVER_POI", entity_id=f"poi_{poi_id}")
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
