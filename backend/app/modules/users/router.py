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
def get_all_users(db: Session = Depends(get_db)):
    service = UserService(db)
    return service.get_all_users()


@router.get("/settings", response_model=schemas.UserSettingsResponse)
def get_user_settings(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    user_id: int = 1,
):
    target_user = current_user
    if not target_user:
        target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return schemas.UserSettingsResponse(exploration_tracking_enabled=True, show_fog=True)
    return target_user


@router.patch("/settings", response_model=schemas.UserSettingsResponse)
def update_user_settings(
    settings_update: schemas.UserSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_current_user),
    user_id: int = 1,
):
    target_user = current_user
    if not target_user:
        target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        return schemas.UserSettingsResponse(exploration_tracking_enabled=True, show_fog=True)

    if settings_update.exploration_tracking_enabled is not None:
        target_user.exploration_tracking_enabled = settings_update.exploration_tracking_enabled
    if settings_update.show_fog is not None:
        target_user.show_fog = settings_update.show_fog

    db.commit()
    db.refresh(target_user)
    return target_user