from datetime import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserFogMap(Base):
    __tablename__ = "user_fog_maps"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    city_id = Column(Integer, nullable=False, default=1)
    unfogged_geometry = Column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=False)
    last_updated_at = Column(DateTime, default=datetime.utcnow)


class DiscoveredArea(Base):
    __tablename__ = "discovered_areas"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    lat = Column(Float, nullable=False)
    lon = Column(Float, nullable=False)
    radius = Column(Float, default=150.0)
    discovered_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("app.modules.users.models.User", back_populates="discovered_areas")