import datetime
from geoalchemy2 import Geometry
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.modules.users.models import User


class DiscoveredArea(Base):
    __tablename__ = "discovered_areas"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    lat = Column(Float)
    lon = Column(Float)
    radius = Column(Float, default=0.15)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow)

    user = relationship("app.modules.users.models.User", back_populates="discovered_areas")


class UserPOIDiscovery(Base):
    __tablename__ = "user_poi_discoveries"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    poi_id = Column(Integer, index=True, nullable=False)
    discovered_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)


class UserPOIState(Base):
    __tablename__ = "user_poi_states"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    poi_id = Column(Integer, index=True, nullable=False)
    state = Column(String(20), index=True, nullable=False)  # 'hidden', 'unknown', 'discovered'
    discovered_at = Column(DateTime, nullable=True)
    discovery_source = Column(String(50), default="system_init")  # 'gps', 'manual', 'route', 'system_init'
    first_discovered_by = Column(String(100), nullable=True)
    first_discovered_at = Column(DateTime, nullable=True)
    discovery_version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class POI(Base):
    __tablename__ = "locations"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    category = Column(String, index=True)
    geometry = Column(Geometry("POINT", srid=4326))
    rarity = Column(String(20), default="common", nullable=False)
    poi_type = Column(String(20), default="standard", nullable=False)
    is_secret = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    details = relationship(
        "app.modules.exploration.models.POIDetail", back_populates="location", uselist=False
    )


class POIDetail(Base):
    __tablename__ = "location_details"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"))

    # 📊 بردار ویژگی‌های اتمسفر و حس‌و‌حال مکان (Vibe Feature Vector)
    nature = Column(Float, default=0.0)
    history = Column(Float, default=0.0)
    crowded = Column(Float, default=0.0)
    quiet = Column(Float, default=0.0)
    nightlife = Column(Float, default=0.0)
    luxury = Column(Float, default=0.0)
    budget = Column(Float, default=0.0)
    romantic = Column(Float, default=0.0)
    family = Column(Float, default=0.0)
    study = Column(Float, default=0.0)
    photography = Column(Float, default=0.0)
    food = Column(Float, default=0.0)

    description = Column(String, nullable=True)

    location = relationship("app.modules.exploration.models.POI", back_populates="details")


class ExplorationEvent(Base):
    __tablename__ = "exploration_events"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False, index=True)
    description = Column(String, nullable=False)
    event_type = Column(String(50), nullable=False, index=True)
    status = Column(String(20), default="scheduled", nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_meters = Column(Float, default=500.0, nullable=False)
    geometry = Column(Geometry("POINT", srid=4326), nullable=False)
    xp_reward = Column(Integer, default=100, nullable=False)
    target_participants = Column(Integer, default=50, nullable=True)
    target_xp = Column(Integer, default=5000, nullable=True)
    community_reward_xp = Column(Integer, default=500, nullable=True)
    starts_at = Column(DateTime, nullable=False)
    ends_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @property
    def current_status(self) -> str:
        now = datetime.datetime.utcnow()
        if self.starts_at and now < self.starts_at:
            return "scheduled"
        if self.ends_at and now >= self.ends_at:
            return "ended"
        return "active"


class ExplorationEventParticipation(Base):
    __tablename__ = "exploration_event_participations"
    __table_args__ = (
        UniqueConstraint("user_id", "event_id", name="uq_user_event_participation"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("exploration_events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    participated_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    distance_meters = Column(Float, nullable=False)
    xp_awarded = Column(Integer, default=0, nullable=False)


class ExplorationEventActivity(Base):
    __tablename__ = "exploration_event_activities"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("exploration_events.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    activity_type = Column(String(50), nullable=False, index=True)  # 'participation', 'challenge_progress', 'challenge_completed'
    title = Column(String(100), nullable=False)
    description = Column(String, nullable=False)
    xp_earned = Column(Integer, default=0, nullable=False)
    progress_pct = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)