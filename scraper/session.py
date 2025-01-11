from fastapi import HTTPException
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from sqlalchemy.orm import Session
from app.models import InstagramSession
from pydantic import BaseModel, ConfigDict

# Request 모델 추가
class SessionRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    username: str
    password: str

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    status: str
    message: str
    username: str

class InstagramSessionManager:
    def __init__(self, username: str, password: str, db: Session):
        self.username = username
        self.password = password
        self.db = db
        self.client = Client()
        
        # 기본 설정
        self.client.delay_range = [1, 3]
        self.client.logger.setLevel('DEBUG')
        self.client.set_locale('en_US')
        self.client.set_timezone_offset(-14400)
        self.client.set_country_code(1)

    def init_session(self):
        """Initialize or load Instagram session"""
        try:
            # DB에서 기존 세션 확인
            existing_session = (
                self.db.query(InstagramSession)
                .filter(InstagramSession.username == self.username)
                .first()
            )
            
            if existing_session:
                print(f"Loading existing session for {self.username}")
                # 세션 상태 확인
                if existing_session.is_block:
                    raise HTTPException(status_code=400, detail="Account is blocked")
                if existing_session.is_challenge:
                    raise HTTPException(status_code=400, detail="Challenge required")
                if existing_session.is_temp_block:
                    raise HTTPException(status_code=400, detail="Account is temporarily blocked")
                
                # 저장된 세션 데이터 로드
                self.client.set_settings(existing_session.session_data)
                try:
                    self.client.get_timeline_feed()
                    print("Session is valid")
                except LoginRequired:
                    print("Session is invalid, performing fresh login")
                    self._perform_login()
            else:
                print("No existing session, performing fresh login")
                self._perform_login()

            # DB 업데이트
            self._update_database()
            
            return {
                "status": "success",
                "message": "Session initialized successfully",
                "username": self.username
            }

        except Exception as e:
            print(f"Session initialization error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={"status": "error", "message": str(e)}
            )

    def _perform_login(self):
        """Perform Instagram login"""
        try:
            login_result = self.client.login(self.username, self.password)
            
            if not login_result:
                raise HTTPException(status_code=400, detail="Login failed")
            
            print("Login successful")
            return login_result
            
        except Exception as e:
            print(f"Login error: {str(e)}")
            raise

    def _update_database(self):
        """Update or create database record"""
        try:
            existing_session = (
                self.db.query(InstagramSession)
                .filter(InstagramSession.username == self.username)
                .first()
            )
            
            session_data = self.client.get_settings()
            
            if existing_session:
                existing_session.password = self.password
                existing_session.session_data = session_data
                existing_session.is_block = False
                existing_session.is_challenge = False
                existing_session.is_temp_block = False
            else:
                new_session = InstagramSession(
                    username=self.username,
                    password=self.password,
                    session_data=session_data,
                    is_block=False,
                    is_challenge=False,
                    is_temp_block=False,
                    number_of_use=0
                )
                self.db.add(new_session)
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            raise

def insta_create_session(data: SessionRequest, db: Session) -> SessionResponse:
    """FastAPI endpoint handler"""
    session_manager = InstagramSessionManager(data.username, data.password, db)
    return session_manager.init_session()
