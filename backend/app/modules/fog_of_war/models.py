from sqlalchemy import Column, Integer, DateTime
from datetime import datetime
from geoalchemy2 import Geometry
from app.core.database import Base

class UserFogMap(Base):
    __tablename__ = "user_fog_maps"

    # Shenaseye yekta baraye har radif
    id = Column(Integer, primary_key=True, index=True)
    
    # Shenaseye karbari ke in mahale ro kashf kardeh
    user_id = Column(Integer, index=True, nullable=False)
    city_id = Column(Integer, nullable=False, default=1)
    
    # In hamoon sotoon e jadooyi e PostGIS hast baraye zakhire kardan e chand-zeli ha (Polygons)
    unfogged_geometry = Column(Geometry(geometry_type='MULTIPOLYGON', srid=4326), nullable=False)
    
    last_updated_at = Column(DateTime, default=datetime.utcnow)