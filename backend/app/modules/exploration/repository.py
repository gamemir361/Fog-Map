import time
from sqlalchemy import func
from app.modules.exploration.models import DiscoveredArea, POI, POIDetail, User

# In-memory cache for BBox and POI queries (<100ms response time)
_POI_CACHE = {}
_CACHE_TTL_SECONDS = 30


def clear_poi_cache():
    global _POI_CACHE
    _POI_CACHE.clear()


def normalize_persian_text(text: str) -> str:
    if not text:
        return ""
    return (
        text.replace("آ", "ا")
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace("ة", "ه")
        .strip()
    )


from sqlalchemy.orm import joinedload


class ExplorationRepository:
    def __init__(self, db):
        self.db = db

    def list_pois(
        self,
        category: str = None,
        search: str = None,
        bbox: str = None,
        limit: int = 100,
        offset: int = 0,
    ):
        query = self.db.query(POI).options(joinedload(POI.details)).join(POIDetail, isouter=True)

        if category and category.lower() != "all":
            query = query.filter(POI.category == category)

        if search:
            norm_search = normalize_persian_text(search)
            pattern = f"%{norm_search}%"

            # Normalize DB columns on the fly for robust Persian Fuzzy Search
            db_norm_name = func.replace(func.replace(POI.name, "آ", "ا"), "ي", "ی")
            db_norm_desc = func.replace(func.replace(POIDetail.description, "آ", "ا"), "ي", "ی")

            query = query.filter(
                db_norm_name.ilike(pattern) | db_norm_desc.ilike(pattern)
            )

        if bbox:
            try:
                parts = [float(p.strip()) for p in bbox.split(",")]
                if len(parts) == 4:
                    min_lon, min_lat, max_lon, max_lat = parts
                    query = query.filter(
                        func.ST_Intersects(
                            POI.geometry,
                            func.ST_MakeEnvelope(min_lon, min_lat, max_lon, max_lat, 4326),
                        )
                    )
            except Exception as exc:
                print("BBox parse warning:", exc)

        results = query.offset(offset).limit(limit).all()
        return results

    def get_user_by_id(self, user_id):
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(self, user_id):
        user = User(id=user_id, username=f"explorer_{user_id}", score=0)
        self.db.add(user)
        return user

    def create_discovered_area(self, user_id, lat, lon):
        area = DiscoveredArea(user_id=user_id, lat=lat, lon=lon)
        self.db.add(area)
        return area

    def list_discovered_areas(self, user_id):
        return self.db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id).all()

    def get_nearest_poi(self, lat, lon):
        clicked_point = f"SRID=4326;POINT({lon} {lat})"
        return (
            self.db.query(POI)
            .order_by(func.ST_Distance(POI.geometry, func.ST_GeomFromText(clicked_point)))
            .first()
        )

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()
