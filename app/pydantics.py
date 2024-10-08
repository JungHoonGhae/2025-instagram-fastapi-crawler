from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BaseProfile(BaseModel):
    username: str


class InstagramPostResponse(BaseModel):
    id: int
    profile: Optional[str]
    loading_time: str
    create_at: datetime

    class Config:
        orm_mode = True


class InstagramSessionResponse(BaseModel):
    id: int
    username: str
    is_block: bool
    is_challenge: bool
    is_temp_block: bool
    number_of_use: int
    session_data: dict

    class Config:
        orm_mode = True


class InstagramSessionUpdate(BaseModel):
    username: Optional[str] = None
    is_block: Optional[bool] = None
    is_challenge: Optional[bool] = None
    is_temp_block: Optional[bool] = None
    number_of_use: Optional[int] = None
    session_data: Optional[dict] = None
