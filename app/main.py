from typing import Dict

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.dependencies import get_db
from app.models import InstagramPosts
from scraper.posts import fetch_instagram_data
from scraper.session import insta_create_session, save_session

app = FastAPI()

"""register models in the database"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.database import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
# Base.metadata.create_all(bind=engine)
"""////////////////////////////////"""


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


class BaseProfile(BaseModel):
    username: str


@app.post("/fetch_posts/")
async def get_instagram_data(request: BaseProfile):
    try:
        # اجرای تابع و بازگرداندن نتیجه در صورت موفقیت
        print(request.username)
        data = await fetch_instagram_data(request.username)
        return {"status": "success", "url": f"http://127.0.0.1:8000/{request.username}"}

    except ValueError as e:
        # اگر خطایی از نوع ValueError رخ داد
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

    except Exception as e:
        # برای هر نوع خطای غیرمنتظره دیگر
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )


def customDecoder(dict_obj):
    # تبدیل custom json به object
    return dict_obj


router = APIRouter()


@app.get("/fetch_posts/{profile_profile}")
def get_profile(
    profile_profile: str,
    limit: int = Query(default=100, ge=1),  # تعداد پست‌ها در هر صفحه (پیش‌فرض 10)
    offset: int = Query(default=0, ge=0),  # چند پست را از ابتدای لیست رد کند (پیش‌فرض 0)
    db: SessionLocal = Depends(get_db),
):
    profile = (
        db.query(InstagramPosts)
        .filter(InstagramPosts.profile == profile_profile)
        .first()
    )

    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")

    # تبدیل json_posts به لیست پست‌ها (فرض شده json_posts یک رشته JSON است)
    posts = profile.json_posts
    if isinstance(posts, str):
        import json

        posts = json.loads(posts)

    # صفحه‌بندی
    paginated_posts = posts[offset : offset + limit]

    return {
        "username": profile_profile,
        "posts": paginated_posts,
        "total_posts": len(posts),
        "limit": limit,
        "offset": offset,
    }
