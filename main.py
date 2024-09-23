from typing import Dict

from fastapi import Depends, FastAPI
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from scraper.session import insta_create_session, save_session

app = FastAPI()

# InstagramSession.metadata.create_all(bind=engine)


@app.get("/")
async def read_root():
    return {"message": "Welcome to InstaScraper API"}


class LoginRequest(BaseModel):
    username: str
    password: str


@app.post("/get_session/")
async def get_session(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await insta_create_session(data, db)


class BaseSession(BaseModel):
    username: str
    password: str
    session_data: Dict


@app.post("/write_json/")
async def update_json(data: BaseSession, db: AsyncSession = Depends(get_db)):
    return await save_session(data, db)
