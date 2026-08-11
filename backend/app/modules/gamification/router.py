from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_optional_current_user
from app.modules.leaderboard.service import get_leaderboard_data
from app.modules.users.models import User

router = APIRouter()


@router.get("/leaderboard")
def get_leaderboard(
    type: str = Query("overall"),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
):
    current_user_id = current_user.id if current_user else None
    return get_leaderboard_data(
        db=db,
        leaderboard_type=type,
        limit=limit,
        current_user_id=current_user_id,
    )