from fastapi import FastAPI

from .views import post_views, session_views

app = FastAPI()

# ثبت روترها
app.include_router(session_views.router)
app.include_router(post_views.router)


@app.get("/")
async def read_root():
    return {"message": "Welcome to InstaScraper API"}
