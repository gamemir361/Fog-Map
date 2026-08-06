import datetime
from sqlalchemy import Column, Integer, String, DateTime
from app.core.database import Base


class UserScore(Base):
    __tablename__ = "user_scores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, unique=True, index=True, nullable=False)
    total_points = Column(Integer, default=0)
    areas_discovered = Column(Integer, default=0)


class XPLog(Base):
    __tablename__ = "xp_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    event_type = Column(String(50), index=True, nullable=False)
    xp_value = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    entity_id = Column(String(100), nullable=True, index=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)