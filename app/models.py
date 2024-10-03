from datetime import datetime

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Session, relationship

from app.database import Base


class InstagramPosts(Base):
    __tablename__ = "insta_posts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("instagram_sessions.id", ondelete="CASCADE"), nullable=True)
    json_posts = Column(JSON, nullable=True)
    profile = Column(String(250), nullable=True)
    loading_time = Column(String(250), nullable=False)
    create_at = Column(DateTime, default=datetime.now())

    # رابطه با مدل InstagramSession
    session = relationship("InstagramSession", back_populates="posts")


    def fill_object(self, db_session, session, json_posts, *args, **kwargs):
        # پر کردن اطلاعات شیء
        session_obj = (
            db_session.query(InstagramSession).filter_by(id=session.id).first()
        )
        if session_obj:
            self.session = session_obj
        self.json_posts = json_posts
        db_session.add(self)
        db_session.commit()

def get_best_session(db: Session):
    return (
        db.query(InstagramSession)
        .filter(InstagramSession.is_block == False)
        .filter(InstagramSession.is_challenge == False)
        .filter(InstagramSession.is_temp_block == False)
        .order_by(InstagramSession.number_of_use)
        .first()
    )

class InstagramSession(Base):
    __tablename__ = "instagram_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    session_data = Column(JSON)

    is_block = Column(Boolean, default=False)
    is_challenge = Column(Boolean, default=False)
    is_temp_block = Column(Boolean, default=False)
    number_of_use = Column(Integer, default=0)

    # رابطه با مدل InstagramPosts
    posts = relationship("InstagramPosts", back_populates="session")
    
    def increment_use(self, db: Session):
        # افزایش مقدار number_of_use به اندازه یک
        self.number_of_use += 1
        # ذخیره تغییرات در دیتابیس
        db.add(self)
        db.commit()
        db.refresh(self)
