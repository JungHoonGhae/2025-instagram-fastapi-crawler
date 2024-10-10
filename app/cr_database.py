from .database import Base, engine

# ساخت جداول در دیتابیس
Base.metadata.create_all(bind=engine)