from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from scraper.posts import fetch_instagram_data

from ..dependencies import get_db
from ..models import InstagramPosts
from ..pydantics import BaseProfile, InstagramPostResponse

router = APIRouter()

@router.get("/posts/", response_model=List[InstagramPostResponse])
async def get_all_posts(db: Session = Depends(get_db)):
    posts = db.query(InstagramPosts).all()
    if not posts:
        raise HTTPException(status_code=404, detail="No posts found")
    return posts



@router.get("/posts/{profile_profile}")
def get_profile(
    profile_profile: str,
    limit: int = Query(default=10, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    profile = (
        db.query(InstagramPosts)
        .filter(InstagramPosts.profile == profile_profile)
        .first()
    )
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")

    posts = profile.json_posts
    if isinstance(posts, str):
        import json

        posts = json.loads(posts)

    paginated_posts = posts[offset : offset + limit]

    return {
        "id": profile.id,
        "username": profile_profile,
        "posts": paginated_posts,
        "total_posts": len(posts),
        "limit": limit,
        "offset": offset,
    }


@router.delete("/posts/{post_id}", response_model=dict)
async def delete_post(post_id: int, db: Session = Depends(get_db)):
    # پیدا کردن پست مورد نظر با id
    post = db.query(InstagramPosts).filter(InstagramPosts.id == post_id).first()

    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # حذف پست
    db.delete(post)
    db.commit()

    return {"detail": "Post deleted successfully"}


@router.post("/fetch_posts/")
async def get_instagram_data(request: BaseProfile):
    try:
        # اجرای تابع و بازگرداندن نتیجه در صورت موفقیت
        print(request.username)
        await fetch_instagram_data(request.username)
    

    except ValueError as e:
        # اگر خطایی از نوع ValueError رخ داد
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

    except Exception as e:
        # برای هر نوع خطای غیرمنتظره دیگر
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )
    return {
        "status": "success",
        "url": f"http://127.0.0.1:8000/posts/{request.username}",
    }
