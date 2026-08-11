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
        existing = self.db.query(User).filter(User.id == user_id).first()
        if existing:
            return existing
        user = User(id=user_id, username=f"explorer_{user_id}", score=0)
        self.db.add(user)
        self.db.flush()
        return user

    def create_discovered_area(self, user_id, lat, lon):
        area = DiscoveredArea(user_id=user_id, lat=lat, lon=lon)
        self.db.add(area)
        return area

    def list_discovered_areas(self, user_id, bbox: str = None):
        query = self.db.query(DiscoveredArea).filter(DiscoveredArea.user_id == user_id)
        if bbox:
            try:
                parts = [float(p.strip()) for p in bbox.split(",")]
                if len(parts) == 4:
                    min_lon, min_lat, max_lon, max_lat = parts
                    query = query.filter(
                        DiscoveredArea.lat.between(min_lat, max_lat),
                        DiscoveredArea.lon.between(min_lon, max_lon),
                    )
            except Exception:
                pass
        return query.all()

    def is_duplicate_area(self, user_id: int, lat: float, lon: float, distance_meters: float = 50.0) -> bool:
        try:
            query = text("""
                SELECT 1 FROM user_fog_maps
                WHERE user_id = :user_id
                  AND ST_DWithin(
                      unfogged_geometry::geography,
                      ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                      :dist
                  )
                LIMIT 1
            """)
            res = self.db.execute(query, {"user_id": user_id, "lat": lat, "lon": lon, "dist": distance_meters}).scalar()
            if res is not None:
                return True
        except Exception:
            pass

        lat_delta = 0.0006
        lon_delta = 0.0007
        nearby = (
            self.db.query(DiscoveredArea)
            .filter(
                DiscoveredArea.user_id == user_id,
                DiscoveredArea.lat.between(lat - lat_delta, lat + lat_delta),
                DiscoveredArea.lon.between(lon - lon_delta, lon + lon_delta),
            )
            .all()
        )
        for area in nearby:
            if area.lat is not None and area.lon is not None:
                d_lat = abs(area.lat - lat) * 111320.0
                d_lon = abs(area.lon - lon) * 111320.0 * 0.8
                if (d_lat * d_lat + d_lon * d_lon) < (distance_meters * distance_meters):
                    return True
        return False

    def list_nearby_pois(self, lat: float, lon: float, radius_meters: float = 200.0):
        try:
            query = text("""
                SELECT id FROM locations
                WHERE ST_DWithin(
                    geometry::geography,
                    ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography,
                    :radius
                )
            """)
            poi_ids = [r[0] for r in self.db.execute(query, {"lat": lat, "lon": lon, "radius": radius_meters}).fetchall()]
            if poi_ids:
                return (
                    self.db.query(POI)
                    .options(joinedload(POI.details))
                    .filter(POI.id.in_(poi_ids))
                    .all()
                )
            return []
        except Exception:
            pass

        from geoalchemy2.shape import to_shape
        lat_delta = 0.0025
        lon_delta = 0.0025
        candidates = (
            self.db.query(POI)
            .options(joinedload(POI.details))
            .all()
        )
        nearby = []
        for p in candidates:
            plat, plon = None, None
            if p.geometry is not None:
                try:
                    pt = to_shape(p.geometry)
                    plat, plon = pt.y, pt.x
                except Exception:
                    pass
            if plat is not None and plon is not None:
                if abs(plat - lat) <= lat_delta and abs(plon - lon) <= lon_delta:
                    d_lat = abs(plat - lat) * 111320.0
                    d_lon = abs(plon - lon) * 111320.0 * 0.8
                    if (d_lat * d_lat + d_lon * d_lon) <= (radius_meters * radius_meters):
                        nearby.append(p)
        return nearby

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
