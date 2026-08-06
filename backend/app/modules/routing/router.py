from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.modules.routing.schemas import DualRouteRequest, DualRouteResponse
from app.modules.routing.service import plan_dual_route, plan_mood_route

router = APIRouter()


class RouteRequest(BaseModel):
    lat: float
    lon: float
    mood: str


@router.post("/plan")
def plan(req: RouteRequest, db: Session = Depends(get_db)):
    return plan_mood_route(db, req.lat, req.lon, req.mood)


@router.post("/dual-plan", response_model=DualRouteResponse)
def dual_plan(req: DualRouteRequest, db: Session = Depends(get_db)):
    return plan_dual_route(
        db,
        origin_lat=req.origin_lat,
        origin_lon=req.origin_lon,
        dest_lat=req.dest_lat,
        dest_lon=req.dest_lon,
        mood=req.mood,
    )