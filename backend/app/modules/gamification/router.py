from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.gamification import models

router = APIRouter()

@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    # 10 nafar e bartar ro bar asas e emtiyaz neshon mide
    top_users = db.query(models.UserScore).order_by(models.UserScore.total_points.desc()).limit(10).all()
    return {"status": "success", "leaderboard": top_users}