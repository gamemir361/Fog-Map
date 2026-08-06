from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    username: str
    phone_number: Optional[str] = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    phone_number: Optional[str] = None
    score: int = 0
    exploration_tracking_enabled: bool = True
    show_fog: bool = True


class UserSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exploration_tracking_enabled: bool = True
    show_fog: bool = True


class UserSettingsUpdate(BaseModel):
    exploration_tracking_enabled: Optional[bool] = None
    show_fog: Optional[bool] = None