from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor
import logging
import time
from instagrapi.exceptions import ChallengeRequired, LoginRequired

from app.database import get_db
from app.models import get_best_session
from instagrapi import Client
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# 요청 모델 추가
class HashtagSearchRequest(BaseModel):
    """
    Request model for multiple hashtag search
    
    Attributes:
        hashtags (List[str]): List of hashtags to search (without # symbol)
        amount_per_tag (int): Number of recent posts to fetch per hashtag (default: 20)
    
    Example:
        {
            "hashtags": ["programming", "python", "javascript"],
            "amount_per_tag": 20
        }
    """
    hashtags: List[str]
    amount_per_tag: Optional[int] = 20

@router.post("/hashtags/search")
def search_multiple_hashtags(
    request: HashtagSearchRequest,
    db: Session = Depends(get_db)
):
    """Search multiple hashtags simultaneously"""
    logger.info(f"Received search request - hashtags: {request.hashtags}, amount_per_tag: {request.amount_per_tag}")
    
    session = get_best_session(db)
    if not session:
        logger.warning("No valid session found")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "code": "NO_SESSION",
                "message": "No valid Instagram session found. Please login first."
            }
        )

    client = Client()
    client.set_settings(session.session_data)
    client.request_timeout = 5

    def fetch_hashtag(hashtag: str):
        try:
            logger.info(f"Fetching posts for hashtag: {hashtag}")
            time.sleep(2)
            
            medias = client.hashtag_medias_recent(
                name=hashtag,
                amount=request.amount_per_tag
            )
            medias.sort(key=lambda x: x.taken_at, reverse=True)
            
            logger.info(f"Successfully fetched {len(medias)} posts for hashtag: {hashtag}")
            return {
                "status": "success",
                "hashtag": hashtag,
                "count": len(medias),
                "posts": [
                    {
                        "id": media.id,
                        "code": media.code,
                        "taken_at": media.taken_at,
                        "media_type": media.media_type,
                        "thumbnail_url": str(media.thumbnail_url),
                        "caption_text": media.caption_text,
                        "like_count": media.like_count,
                        "comment_count": media.comment_count,
                        "user": {
                            "pk": media.user.pk,
                            "username": media.user.username,
                            "full_name": media.user.full_name,
                            "profile_pic_url": str(media.user.profile_pic_url)
                        },
                        "url": f"https://www.instagram.com/p/{media.code}/",
                        "taken_at_formatted": media.taken_at.strftime("%Y-%m-%d %H:%M:%S")
                    } for media in medias
                ]
            }
            
        except (ChallengeRequired, LoginRequired) as e:
            logger.error(f"Challenge/Login required for hashtag {hashtag}: {str(e)}")
            
            # Update session status using PUT endpoint
            session_update = {
                "username": session.username,
                "is_block": True,
                "is_challenge": True,
                "is_temp_block": False,
                "number_of_use": session.number_of_use,
                "session_data": session.session_data
            }
            
            try:
                # Update session status
                db.query(InstagramSession).filter(InstagramSession.id == session.id).update(session_update)
                db.commit()
                logger.info(f"Session {session.id} marked as blocked and challenged")
            except Exception as db_error:
                logger.error(f"Failed to update session status: {str(db_error)}")
                db.rollback()

            # Extract phone number from error message
            error_msg = str(e)
            phone_number = None
            if "'phone_number':" in error_msg:
                try:
                    import json
                    import re
                    json_str = re.search(r'\{.*\}', error_msg).group()
                    data = json.loads(json_str)
                    phone_number = data.get('step_data', {}).get('phone_number')
                except:
                    pass

            return {
                "status": "error",
                "hashtag": hashtag,
                "error": str(e),
                "error_type": "challenge",
                "challenge_info": {
                    "type": "phone_verification",
                    "phone_number": phone_number,
                    "message": "Please verify your account through SMS"
                },
                "posts": []
            }
        except Exception as e:
            logger.error(f"Error fetching hashtag {hashtag}: {str(e)}")
            
            # Update session status for other errors
            session_update = {
                "username": session.username,
                "is_block": False,
                "is_challenge": False,
                "is_temp_block": True,  # Temporary block for other errors
                "number_of_use": session.number_of_use + 1,
                "session_data": session.session_data
            }
            
            try:
                db.query(InstagramSession).filter(InstagramSession.id == session.id).update(session_update)
                db.commit()
                logger.info(f"Session {session.id} marked as temporarily blocked")
            except Exception as db_error:
                logger.error(f"Failed to update session status: {str(db_error)}")
                db.rollback()

            return {
                "status": "error",
                "hashtag": hashtag,
                "error": str(e),
                "posts": []
            }

    # 병렬로 해시태그 검색 실행
    with ThreadPoolExecutor(max_workers=min(len(request.hashtags), 2)) as executor:
        results = list(executor.map(fetch_hashtag, request.hashtags))

    # 모든 결과가 에러인지 확인
    all_failed = all(result.get("status") == "error" for result in results)
    
    if all_failed:
        # 챌린지 에러가 있는지 확인
        challenge_results = [r for r in results if r.get("error_type") == "challenge"]
        if challenge_results:
            # 첫 번째 챌린지 정보 사용
            challenge_info = challenge_results[0]["challenge_info"]
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "error",
                    "code": "INSTAGRAM_CHALLENGE",
                    "message": "Instagram security check required",
                    "challenge_info": challenge_info
                }
            )
        else:
            # 일반 에러
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "error",
                    "code": "ALL_REQUESTS_FAILED",
                    "message": "All hashtag searches failed",
                    "errors": [{"hashtag": r["hashtag"], "error": r["error"]} for r in results]
                }
            )

    # 일부 성공한 경우만 여기에 도달
    return {
        "status": "partial_success" if any(result.get("status") == "error" for result in results) else "success",
        "results": results
    }