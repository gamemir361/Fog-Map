from sqlalchemy.orm import Session
from app.modules.exploration.models import POI, POIDetail


class RoutingRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_pois_for_mood(self, mood: str, limit: int = 3):
        query = self.db.query(POI).join(POIDetail)

        if mood == "nature":
            if hasattr(POIDetail, "scenic_score") and hasattr(POIDetail, "walkability"):
                return query.order_by(POIDetail.scenic_score.desc(), POIDetail.walkability.desc()).limit(limit).all()
            return query.order_by(POIDetail.nature.desc()).limit(limit).all()
        elif mood == "culture":
            return query.order_by(POIDetail.history.desc(), POIDetail.study.desc()).limit(limit).all()
        elif mood == "energy":
            return query.order_by(POIDetail.crowded.desc(), POIDetail.food.desc()).limit(limit).all()

        return query.limit(limit).all()
