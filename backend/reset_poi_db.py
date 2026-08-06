import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine
from app.modules.exploration.models import POI, POIDetail

def reset_poi_tables():
    print("🗑️ Dar hale pak kardane table haye ghadimi (faghat POI)...")
    # اول جدول جزئیات رو پاک می‌کنیم چون به جدول اصلی وصله
    POIDetail.__table__.drop(engine, checkfirst=True)
    POI.__table__.drop(engine, checkfirst=True)
    
    print("🏗️ Dar hale sakhte table haye jadid ba column haye jadid (vibe_tags, walkability, ...)")
    POI.__table__.create(engine, checkfirst=True)
    POIDetail.__table__.create(engine, checkfirst=True)
    
    print("✅ Table ha ba movafaghiat update shodan!")

if __name__ == "__main__":
    reset_poi_tables()