from sqlalchemy.orm import Session
from app.modules.missions.models import Mission, UserBadge, UserMission


class MissionsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_active_missions(self):
        return self.db.query(Mission).filter(Mission.active.is_(True)).all()

    def get_mission_count(self):
        return self.db.query(Mission).count()

    def create_missions_bulk(self, missions_list):
        self.db.add_all(missions_list)
        self.db.commit()

    def get_user_mission(self, user_id: int, mission_id: int):
        return (
            self.db.query(UserMission)
            .filter(UserMission.user_id == user_id, UserMission.mission_id == mission_id)
            .first()
        )

    def get_all_user_missions(self, user_id: int):
        return self.db.query(UserMission).filter(UserMission.user_id == user_id).all()

    def create_user_mission(self, user_id: int, mission_id: int, progress: int = 0):
        user_mission = UserMission(user_id=user_id, mission_id=mission_id, progress=progress)
        self.db.add(user_mission)
        self.db.flush()
        return user_mission

    def get_user_badges(self, user_id: int):
        return self.db.query(UserBadge).filter(UserBadge.user_id == user_id).all()

    def grant_badge(self, user_id: int, badge_name: str, badge_icon: str = "⭐"):
        existing = (
            self.db.query(UserBadge)
            .filter(UserBadge.user_id == user_id, UserBadge.badge_name == badge_name)
            .first()
        )
        if not existing:
            badge = UserBadge(user_id=user_id, badge_name=badge_name, badge_icon=badge_icon)
            self.db.add(badge)
            self.db.flush()
            return badge
        return existing
