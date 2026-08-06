import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.modules.exploration.models import POI, POIDetail

def check_data():
    db = SessionLocal()
    print("🔍 Checking database for stored POIs...")
    
    # Query kardan e tamame POI ha ba details
    pois = db.query(POI).all()
    
    if not pois:
        print("⚠️ Database is empty! Please run 'python scraper.py' first.")
    else:
        for poi in pois:
            details = poi.details
            if details:
                print(f"✅ Found: {poi.name} | Vibe: {details.vibe_tags} | Walk: {details.walkability} | View: {details.scenic_score}")
            else:
                print(f"⚠️ Found: {poi.name} but no details found!")
    
    db.close()

if __name__ == "__main__":
    check_data()