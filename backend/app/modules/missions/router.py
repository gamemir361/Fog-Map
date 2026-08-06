from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_optional_current_user
from app.modules.missions.service import get_user_gamification_profile, list_active_missions
from app.modules.users.models import User

router = APIRouter()


@router.get("/missions")
def list_missions(db: Session = Depends(get_db)):
    missions = list_active_missions(db)
    return {
        "status": "success",
        "missions": [
            {
                "id": mission.id,
                "title": mission.title,
                "description": mission.description,
                "target": mission.target,
                "reward_points": mission.reward_points,
                "badge_name": mission.badge_name,
                "badge_icon": mission.badge_icon,
            }
            for mission in missions
        ],
    }


@router.get("/missions/profile")
def get_user_profile(
    user_id: int = 1,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    target_user_id = current_user.id if current_user else user_id
    return get_user_gamification_profile(db, user_id=target_user_id)
