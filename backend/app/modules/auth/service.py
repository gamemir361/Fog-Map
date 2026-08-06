from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.security.jwt import create_access_token, hash_password, verify_password
from app.modules.auth.repository import AuthRepository
from app.modules.auth.schemas import TokenResponse, UserAuthResponse, UserLoginRequest, UserRegisterRequest
from app.modules.users.models import User


class AuthService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = AuthRepository(db)

    def register(self, data: UserRegisterRequest) -> TokenResponse:
        username = data.username.strip()
        if not username:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="نام کاربری نمی‌تواند خالی باشد.")

        if self.repo.get_by_username(username):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="این نام کاربری قبلاً ثبت شده است.")

        if data.email and self.repo.get_by_email(data.email):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="این ایمیل قبلاً ثبت شده است.")

        if len(data.password) < 4:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="رمز عبور باید حداقل ۴ کاراکتر باشد.")

        hashed_pw = hash_password(data.password)
        user = self.repo.create_user(
            username=username,
            hashed_password=hashed_pw,
            email=data.email,
            phone_number=data.phone_number,
        )

        token = create_access_token({"sub": user.id})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserAuthResponse.model_validate(user),
        )

    def login(self, data: UserLoginRequest) -> TokenResponse:
        username = data.username.strip()
        user = self.repo.get_by_username(username)
        if not user and "@" in username:
            user = self.repo.get_by_email(username)

        if not user or not verify_password(data.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="نام کاربری یا رمز عبور اشتباه است.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = create_access_token({"sub": user.id})
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            user=UserAuthResponse.model_validate(user),
        )
