from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import Base, engine, get_db
from app.modules.auth.router import router as auth_router
from app.modules.fog_of_war import models as fog_models
from app.modules.fog_of_war.router import router as fog_router
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
        conn.commit()
    Base.metadata.create_all(bind=engine)
except Exception as exc:
    print("Database init info:", exc)

app = FastAPI(
    title="Fog Map & Heatmap Platform",
    description="Minimal geospatial platform focused on atmospheric Fog of War exploration and personal Heatmap visualization.",
    version="2.0.0",
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(users_router, prefix="/api/v1/users", tags=["Users"])
app.include_router(fog_router, prefix="/api/v1/fog", tags=["Fog of War"])


@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok, database connected!"
    except Exception as e:
        db_status = f"error: {str(e)}"
    return {"status": "ok", "database": db_status}