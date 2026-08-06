from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Mission(Base):
    __tablename__ = "missions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(String(255), nullable=False)
    event_type = Column(String(50), default="discover_area")
    conditions_json = Column(Text, nullable=True)
    badge_name = Column(String(100), nullable=True)
    badge_icon = Column(String(20), nullable=True)
    target = Column(Integer, default=1)
    reward_points = Column(Integer, default=10)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class UserMission(Base):
    __tablename__ = "user_missions"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    mission_id = Column(Integer, ForeignKey("missions.id"))
    progress = Column(Integer, default=0)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime, nullable=True)

    mission = relationship("Mission")


class UserBadge(Base):
    __tablename__ = "user_badges"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)
    badge_name = Column(String(100), nullable=False)
    badge_icon = Column(String(20), default="⭐")
    unlocked_at = Column(DateTime, default=datetime.utcnow)
