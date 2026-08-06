import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
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
    score = Column(Integer, default=0)
    exploration_tracking_enabled = Column(Boolean, default=True, nullable=False)
    show_fog = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    # 🧠 بردار ترجیحات کاربر (User Preference Vector)
    pref_nature = Column(Float, default=0.5)
    pref_history = Column(Float, default=0.5)
    pref_crowded = Column(Float, default=0.5)
    pref_quiet = Column(Float, default=0.5)
    pref_nightlife = Column(Float, default=0.5)
    pref_luxury = Column(Float, default=0.5)
    pref_budget = Column(Float, default=0.5)
    pref_romantic = Column(Float, default=0.5)
    pref_family = Column(Float, default=0.5)
    pref_study = Column(Float, default=0.5)
    pref_photography = Column(Float, default=0.5)
    pref_food = Column(Float, default=0.5)

    discovered_areas = relationship(
        "app.modules.exploration.models.DiscoveredArea", back_populates="user"
    )