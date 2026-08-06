import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import SessionLocal
from app.modules.exploration.models import POI, POIDetail

# تعریف نقاط تستی با بردارهای حس‌و‌حال (Vibe Vectors)
mock_pois = [
    {
        "name": "بام محک (دارآباد)",
        "category": "nature",
        "lat": 35.8183, "lon": 51.4871,
        "desc": "منطقه‌ای دنج در ارتفاعات تهران با ویوی عالی.",
        "vectors": {"nature": 0.9, "history": 0.1, "crowded": 0.2, "quiet": 0.8, "nightlife": 0.6, "luxury": 0.4, "budget": 0.8, "romantic": 0.7, "family": 0.6, "study": 0.1, "photography": 0.9, "food": 0.3}
    },
    {
        "name": "خیابان سی‌تیر",
        "category": "food",
        "lat": 35.6908, "lon": 51.4146,
        "desc": "خیابان سنگ‌فرش تاریخی و مرکز غذاهای خیابانی تهران.",
        "vectors": {"nature": 0.1, "history": 0.8, "crowded": 0.9, "quiet": 0.1, "nightlife": 0.9, "luxury": 0.2, "budget": 0.7, "romantic": 0.4, "family": 0.8, "study": 0.0, "photography": 0.7, "food": 1.0}
    },
    {
        "name": "کافه تهرون (ویلا)",
        "category": "cafe",
        "lat": 35.7075, "lon": 51.4170,
        "desc": "کافه‌ای در یک خانه قدیمی و تاریخی با اتمسفر نوستالژیک.",
        "vectors": {"nature": 0.3, "history": 0.9, "crowded": 0.4, "quiet": 0.8, "nightlife": 0.3, "luxury": 0.6, "budget": 0.5, "romantic": 0.8, "family": 0.5, "study": 0.9, "photography": 0.6, "food": 0.8}
    },
    {
        "name": "پل طبیعت",
        "category": "landmark",
        "lat": 35.7540, "lon": 51.4200,
        "desc": "پل پیاده‌روی مدرن که دو پارک بزرگ را به هم وصل می‌کند.",
        "vectors": {"nature": 0.8, "history": 0.1, "crowded": 0.8, "quiet": 0.3, "nightlife": 0.7, "luxury": 0.5, "budget": 0.9, "romantic": 0.8, "family": 0.9, "study": 0.2, "photography": 0.9, "food": 0.6}
    }
]

def run_scraper():
    print("🚀 Start kardane robot e ma'danchi (Vector Edition)...")
    db = SessionLocal()
    try:
        for item in mock_pois:
            # ذخیره مکان در جدول locations
            wkt_geom = f"SRID=4326;POINT({item['lon']} {item['lat']})"
            poi = POI(name=item["name"], category=item["category"], geometry=wkt_geom)
            db.add(poi)
            db.flush() # برای گرفتن ID مکان
            
            # ذخیره بردارها در جدول location_details
            v = item["vectors"]
            detail = POIDetail(
                location_id=poi.id,
                description=item["desc"],
                nature=v["nature"], history=v["history"], crowded=v["crowded"],
                quiet=v["quiet"], nightlife=v["nightlife"], luxury=v["luxury"],
                budget=v["budget"], romantic=v["romantic"], family=v["family"],
                study=v["study"], photography=v["photography"], food=v["food"]
            )
            db.add(detail)
            print(f"✅ {item['name']} ba profil e bordari sabt shod.")
        
        db.commit()
        print("🎉 Tammam e dadeh ha ba memari e Vibe Vectors zakhire shodand!")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    run_scraper()