from typing import Optional
from sqlalchemy.orm import Session
from app.modules.users.models import User


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def create_user(
        self,
        username: str,
        hashed_password: str,
        email: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> User:
        user = User(
            username=username,
            hashed_password=hashed_password,
            email=email,
            phone_number=phone_number,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
