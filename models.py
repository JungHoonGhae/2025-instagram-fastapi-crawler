from sqlalchemy import JSON, Column, Integer, String

from database import Base


class InstagramSession(Base):
    __tablename__ = "instagram_sessions"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    session_data = Column(JSON)
