from typing import List

from pydantic import BaseModel


class ImageSerializer(BaseModel):
    # فرض بر این است که ساختار Image مشخص باشد
    url: str
    alt_text: str


class JsonToObj(BaseModel):
    caption: str
    likes: int
    comments: int
    imgs: List[ImageSerializer]
    reels: str

    class Config:
        orm_mode = True
