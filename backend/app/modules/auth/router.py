from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.deps import get_current_user
from app.modules.auth import schemas
from app.modules.auth.service import AuthService
from app.modules.users.models import User

router = APIRouter()


@router.post("/register", response_model=schemas.TokenResponse)
def register_user(data: schemas.UserRegisterRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.register(data)


@router.post("/login", response_model=schemas.TokenResponse)
def login_user(data: schemas.UserLoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    return service.login(data)


@router.post("/logout")
def logout_user():
    return {"status": "success", "message": "با موفقیت خارج شدید."}


@router.get("/me", response_model=schemas.UserAuthResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user
