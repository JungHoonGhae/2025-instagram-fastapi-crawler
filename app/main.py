from fastapi import FastAPI

from .views import post_views, session_views

app = FastAPI()

app.include_router(session_views.router)
app.include_router(post_views.router)


# """
from .database import Base, engine

# Create a detabase
Base.metadata.create_all(bind=engine)
# """


@app.get("/")
async def read_root():
    return {"message": "Welcome to InstaScraper API"}
