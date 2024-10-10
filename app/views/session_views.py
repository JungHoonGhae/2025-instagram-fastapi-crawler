from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from scraper.session import insta_create_session

from ..dependencies import get_db
from ..models import InstagramSession
from ..pydantics import InstagramSessionResponse, InstagramSessionUpdate

router = APIRouter()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/init-session/")
async def initialize_session(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    print("start initialize_session")
    return await insta_create_session(data, db)


@router.get("/sessions/", response_model=List[InstagramSessionResponse])
def get_sessions(db: Session = Depends(get_db)):
    sessions = db.query(InstagramSession).all()
    return sessions


@router.get("/sessions/{session_id}", response_model=InstagramSessionResponse)
def get_session_detail(session_id: int, db: Session = Depends(get_db)):
    session = (
        db.query(InstagramSession).filter(InstagramSession.id == session_id).first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.put("/sessions/{session_id}", response_model=InstagramSessionResponse)
def update_session(
    session_id: int,
    session_update: InstagramSessionUpdate,
    db: Session = Depends(get_db),
):
    session = (
        db.query(InstagramSession).filter(InstagramSession.id == session_id).first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # بروزرسانی فیلدها
    if session_update.username:
        session.username = session_update.username
    if session_update.is_block is not None:
        session.is_block = session_update.is_block
    if session_update.is_challenge is not None:
        session.is_challenge = session_update.is_challenge
    if session_update.is_temp_block is not None:
        session.is_temp_block = session_update.is_temp_block
    if session_update.number_of_use is not None:
        session.number_of_use = session_update.number_of_use
    if session_update.session_data is not None:
        session.session_data = session_update.session_data

    db.commit()
    db.refresh(session)
    return session


@router.delete("/sessions/{session_id}", response_model=dict)
def delete_session(session_id: int, db: Session = Depends(get_db)):
    session = (
        db.query(InstagramSession).filter(InstagramSession.id == session_id).first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    db.delete(session)
    db.commit()
    return {"detail": "Session deleted successfully"}
