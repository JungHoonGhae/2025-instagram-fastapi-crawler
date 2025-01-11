from fastapi import FastAPI

from .views import post_views, session_views, hashtag_views
from .database import init_db

app = FastAPI()

# 앱 시작 시 데이터베이스 초기화
@app.on_event("startup")
async def startup_event():
    init_db()

app.include_router(session_views.router)
app.include_router(post_views.router)
app.include_router(hashtag_views.router)


# """
from .database import Base, engine

# Create a detabase
Base.metadata.create_all(bind=engine)
# """


@app.get("/")
async def read_root():
    return {"message": "Welcome to InstaScraper API"}
