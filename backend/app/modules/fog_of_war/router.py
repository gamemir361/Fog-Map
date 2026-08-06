from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_current_user
from app.modules.fog_of_war import schemas
from app.modules.fog_of_war.service import get_fog_statistics, process_fog_discovery
from app.modules.users.models import User

router = APIRouter()


@router.post("/discover")
def discover_new_area(
    location: schemas.LocationDiscover,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    target_user_id = current_user.id if current_user else (location.user_id or 1)
    return process_fog_discovery(db, target_user_id, location.lat, location.lon)


@router.get("/stats", response_model=schemas.FogStatsResponse)
def get_stats(
    user_id: int = 1,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    target_user_id = current_user.id if current_user else user_id
    return get_fog_statistics(db, target_user_id)