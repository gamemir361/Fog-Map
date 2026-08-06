import json
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.modules.fog_of_war.models import UserFogMap
from app.modules.gamification.models import UserScore

TEHRAN_TOTAL_AREA_SQM = 730000000.0  # ~730 km²


class FogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_user_centroids(self, user_id: int):
        return (
            self.db.query(
                func.ST_Y(func.ST_Centroid(UserFogMap.unfogged_geometry)).label("lat"),
                func.ST_X(func.ST_Centroid(UserFogMap.unfogged_geometry)).label("lon"),
            )
            .filter(UserFogMap.user_id == user_id)
            .all()
        )

    def add_fog_discovery(self, user_id: int, lat: float, lon: float, radius_meters: float = 150.0):
        # Create a PostGIS circular buffer polygon of radius_meters around (lon, lat)
        wkt = f"SRID=4326;POLYGON(({lon - 0.002} {lat - 0.002}, {lon + 0.002} {lat - 0.002}, {lon + 0.002} {lat + 0.002}, {lon - 0.002} {lat + 0.002}, {lon - 0.002} {lat - 0.002}))"

        try:
            # Attempt PostGIS true circular buffer query
            buffer_query = text(
                "SELECT ST_AsEWKT(ST_Multi(ST_Buffer(ST_SetSRID(ST_MakePoint(:lon, :lat), 4326)::geography, :radius)::geometry));"
            )
            res = self.db.execute(buffer_query, {"lon": lon, "lat": lat, "radius": radius_meters}).scalar()
            if res:
                wkt = res
        except Exception:
            pass

        # Use PostGIS function to convert EWKT string to geometry
        geometry = text('SELECT ST_GeomFromEWKT(:wkt)')
        geom_result = self.db.execute(geometry, {'wkt': wkt}).scalar()
        discovery = UserFogMap(user_id=user_id, unfogged_geometry=geom_result)
        self.db.add(discovery)
        return discovery

    def get_user_coverage_stats(self, user_id: int):
        # Calculate total area using PostGIS ST_Union and ST_Area
        total_sqm = 0.0
        geojson_geom = None

        try:
            area_query = text(
                """
                SELECT ST_Area(ST_Union(unfogged_geometry)::geography) as area_sqm,
                       ST_AsGeoJSON(ST_Union(unfogged_geometry)) as geojson
                FROM user_fog_maps
                WHERE user_id = :user_id
                """
            )
            res = self.db.execute(area_query, {"user_id": user_id}).fetchone()
            if res and res.area_sqm is not None:
                total_sqm = float(res.area_sqm)
            if res and res.geojson:
                geojson_geom = json.loads(res.geojson)
        except Exception as exc:
            # Fallback estimation based on centroid counts if non-PostGIS
            centroids = self.get_user_centroids(user_id)
            total_sqm = len(centroids) * 70685.8  # pi * 150^2

        total_sqkm = round(total_sqm / 1000000.0, 4)
        coverage_pct = round(min(100.0, (total_sqm / TEHRAN_TOTAL_AREA_SQM) * 100), 6)

        return {
            "total_area_sqm": round(total_sqm, 2),
            "total_area_sqkm": total_sqkm,
            "city_coverage_percentage": coverage_pct,
            "geojson_geometry": geojson_geom,
        }

    def get_or_create_user_score(self, user_id: int, initial_points: int):
        user_score = self.db.query(UserScore).filter(UserScore.user_id == user_id).first()
        if not user_score:
            user_score = UserScore(user_id=user_id, total_points=initial_points, areas_discovered=1)
            self.db.add(user_score)
        return user_score

    def commit(self):
        self.db.commit()
