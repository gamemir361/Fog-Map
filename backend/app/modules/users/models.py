import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=True)
    role = Column(String(20), default="USER", nullable=False)
    phone_number = Column(String(15), nullable=True)
    exploration_tracking_enabled = Column(Boolean, default=True, nullable=False)
    show_fog = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    discovered_areas = relationship(
        "app.modules.fog_of_war.models.DiscoveredArea", back_populates="user"
    )