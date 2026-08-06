import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
from app.modules.exploration.models import User, DiscoveredArea, POI, POIDetail

def run_migration():
    print("🗑️ Dar hale pak kardane table haye ghadimi...")
    POIDetail.__table__.drop(engine, checkfirst=True)
    DiscoveredArea.__table__.drop(engine, checkfirst=True)
    POI.__table__.drop(engine, checkfirst=True)
    User.__table__.drop(engine, checkfirst=True)
    
    print("🏗️ Dar hale sakhte table haye jadid ba memari e bordari (Feature Vectors)...")
    Base.metadata.create_all(bind=engine)
    print("✅ Memari e jadid ba movafaghiat dar ditabase e'mal shod!")

if __name__ == "__main__":
    run_migration()