from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user, get_optional_current_user
from app.modules.users import schemas
from app.modules.users.models import User
from app.modules.users.service import UserService

router = APIRouter()


@router.post("/", response_model=schemas.UserResponse)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    service = UserService(db)
    return service.create_user(user)


@router.get("/", response_model=list[schemas.UserResponse])
def get_all_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    return service.get_all_users()


@router.get("/settings", response_model=schemas.UserSettingsResponse)
def get_user_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.patch("/settings", response_model=schemas.UserSettingsResponse)
def update_user_settings(
    settings_update: schemas.UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if settings_update.exploration_tracking_enabled is not None:
        current_user.exploration_tracking_enabled = settings_update.exploration_tracking_enabled
    if settings_update.show_fog is not None:
        current_user.show_fog = settings_update.show_fog

    db.commit()
    db.refresh(current_user)
    return current_user