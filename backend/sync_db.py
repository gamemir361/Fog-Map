import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import engine, Base
# ایمپورت کردن تمام مدل‌ها برای اینکه SQLAlchemy بشناسدشون
from app.modules.exploration.models import User, DiscoveredArea, POI, POIDetail

def sync_database():
    print("🏗️ Dar hale barresi va sakhte table haye jadid (users, discovered_areas)...")
    # این دستور فقط جدول‌هایی که وجود ندارن رو می‌سازه و به قبلی‌ها دست نمی‌زنه
    Base.metadata.create_all(bind=engine)
    print("✅ Table ha ba movafaghiat sakhte shodan!")

if __name__ == "__main__":
    sync_database()
