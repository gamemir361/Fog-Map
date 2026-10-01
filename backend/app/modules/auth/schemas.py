from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserRegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    phone_number: Optional[str] = None


class UserLoginRequest(BaseModel):
    username: str
    password: str


class UserAuthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    role: str = "USER"
    email: Optional[str] = None
    phone_number: Optional[str] = None
    exploration_tracking_enabled: bool = True
    show_fog: bool = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserAuthResponse
