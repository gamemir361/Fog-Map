import sys
import os
import math

# Add backend directory to sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.modules.fog_of_war.service import get_distance_meters, process_fog_discovery, get_fog_statistics
from app.modules.fog_of_war.repository import FogRepository
from app.core.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

print("--- Testing Backend 50m vs 150m Radius and Math Logic ---")

# 1. Test Haversine distance accuracy
tehran_lat, tehran_lon = 35.6892, 51.3890

# Calculate offset for 49.9m, 50.0m, 50.1m, 149.9m, 150.0m north
# 1 degree latitude ~ 111,000 meters
def lat_offset_meters(meters):
    return meters / 111000.0

lat_0 = tehran_lat
lon_0 = tehran_lon

lat_49_9 = tehran_lat + lat_offset_meters(49.9)
lat_50_0 = tehran_lat + lat_offset_meters(50.0)
lat_50_1 = tehran_lat + lat_offset_meters(50.1)
lat_149_9 = tehran_lat + lat_offset_meters(149.9)
lat_150_0 = tehran_lat + lat_offset_meters(150.0)

dist_49_9 = get_distance_meters(lat_0, lon_0, lat_49_9, lon_0)
dist_50_0 = get_distance_meters(lat_0, lon_0, lat_50_0, lon_0)
dist_50_1 = get_distance_meters(lat_0, lon_0, lat_50_1, lon_0)
dist_149_9 = get_distance_meters(lat_0, lon_0, lat_149_9, lon_0)
dist_150_0 = get_distance_meters(lat_0, lon_0, lat_150_0, lon_0)

print(f"Distance for 49.9m target: {dist_49_9:.2f}m")
print(f"Distance for 50.0m target: {dist_50_0:.2f}m")
print(f"Distance for 50.1m target: {dist_50_1:.2f}m")
print(f"Distance for 149.9m target: {dist_149_9:.2f}m")
print(f"Distance for 150.0m target: {dist_150_0:.2f}m")

# 2. In-memory SQLite Database Integration Test
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = TestingSessionLocal()

user_id = 101

# Step A: Initial discovery at (lat_0, lon_0)
res1 = process_fog_discovery(db, user_id, lat_0, lon_0)
print("\nStep A (Initial Discovery):")
print("  Status:", res1["status"])
print("  Points granted:", res1["current_points"] == 10, f"(Points: {res1['current_points']})")

# Step B: Duplicate discovery at distance < 50m (dist_49_9)
res2 = process_fog_discovery(db, user_id, lat_49_9, lon_0)
print("\nStep B (Discovery at 49.9m - Duplicate):")
print("  Points granted:", res2["current_points"] == 10, f"(Points: {res2['current_points']})")
print("  Message Persian:", res2["message"])

# Step C: Valid discovery at distance > 50m (dist_50_1)
res3 = process_fog_discovery(db, user_id, lat_50_1, lon_0)
print("\nStep C (Discovery at 50.1m - Valid):")
print("  Points granted:", res3["current_points"] == 20, f"(Points: {res3['current_points']})")
print("  Message Persian:", res3["message"])

# Step D: Check fallback SQM math
stats = get_fog_statistics(db, user_id)
print("\nStep D (Fallback Area Statistics):")
print("  Areas Discovered Count:", stats["areas_discovered_count"])
print("  Total Area SQM:", stats["total_area_sqm"], f"(Expected ~ {3 * 70685.8})")
print("  Total Area SQKM:", stats["total_area_sqkm"])

# Verification Assertion
assert res1["current_points"] == 10, "Initial discovery should grant 10 points"
assert res2["current_points"] == 10, "Duplicate discovery (<50m) should NOT grant points"
assert res3["current_points"] == 20, "Valid discovery (>50m) SHOULD grant 10 points"
assert stats["areas_discovered_count"] == 3, "Total discovery records in DB should be 3"
assert math.isclose(stats["total_area_sqm"], 212057.4, abs_tol=1.0), "Fallback SQM calculation mismatch"

print("\n--- ALL BACKEND LOGIC CHECKS PASSED ---")
