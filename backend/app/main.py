from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import Base, SessionLocal, engine, get_db
from app.modules.auth.router import router as auth_router
from app.modules.exploration import models as exploration_models
from app.modules.exploration.router import router as exploration_router
from app.modules.exploration.seed import seed_exploration_data
from app.modules.fog_of_war import models as fog_models
from app.modules.fog_of_war.router import router as fog_router
from app.modules.gamification import models as game_models
from app.modules.gamification.router import router as game_router
from app.modules.missions import models as missions_models
from app.modules.missions.router import router as missions_router
from app.modules.missions.service import seed_missions
from app.modules.routing.router import router as routing_router
from app.modules.users import models as users_models
from app.modules.users.router import router as users_router

try:
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(15);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(100);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS hashed_password VARCHAR(255);"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'USER';"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS exploration_tracking_enabled BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS show_fog BOOLEAN DEFAULT TRUE;"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;"))
        conn.execute(text("ALTER TABLE missions ADD COLUMN IF NOT EXISTS event_type VARCHAR(50) DEFAULT 'discover_area';"))
        conn.execute(text("ALTER TABLE missions ADD COLUMN IF NOT EXISTS conditions_json TEXT;"))
        conn.execute(text("ALTER TABLE missions ADD COLUMN IF NOT EXISTS badge_name VARCHAR(100);"))
        conn.execute(text("ALTER TABLE missions ADD COLUMN IF NOT EXISTS badge_icon VARCHAR(20);"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS xp_logs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                event_type VARCHAR(50) NOT NULL,
                xp_value INTEGER NOT NULL,
                reason VARCHAR(255),
                entity_id VARCHAR(100),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_poi_discoveries (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                poi_id INTEGER NOT NULL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, poi_id)
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS user_poi_states (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL,
                poi_id INTEGER NOT NULL,
                state VARCHAR(20) NOT NULL,
                discovered_at TIMESTAMP,
                discovery_source VARCHAR(50) DEFAULT 'system_init',
                first_discovered_by VARCHAR(100),
                first_discovered_at TIMESTAMP,
                discovery_version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, poi_id)
            );
        """))
        conn.execute(text("ALTER TABLE locations ADD COLUMN IF NOT EXISTS rarity VARCHAR(20) DEFAULT 'common';"))
        conn.execute(text("ALTER TABLE locations ADD COLUMN IF NOT EXISTS poi_type VARCHAR(20) DEFAULT 'standard';"))
        conn.execute(text("ALTER TABLE locations ADD COLUMN IF NOT EXISTS is_secret BOOLEAN DEFAULT FALSE;"))
        conn.execute(text("ALTER TABLE locations ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)
    seed_exploration_data()
    with SessionLocal() as session:
        seed_missions(session)
except Exception as exc:
    print("Database init info:", exc)

app = FastAPI(
    title="Urban Exploration Platform",
    description="Solid foundation for geospatial and gamified urban exploration.",
    version="1.0.0",
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(routing_router, prefix="/api/v1/routes", tags=["Routes"])
app.include_router(fog_router, prefix="/api/v1/fog", tags=["Fog of War"])
app.include_router(game_router, prefix="/api/v1/gamification", tags=["Gamification"])
app.include_router(exploration_router, prefix="/api/v1/exploration", tags=["Exploration"])
app.include_router(missions_router, prefix="/api/v1", tags=["Missions"])


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok, database connected!"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "ok", "database": db_status}