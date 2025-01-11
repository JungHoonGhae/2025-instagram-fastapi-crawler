from typing import List, Optional, Tuple
from instagrapi.types import Media
from sqlalchemy.orm import Session
from fastapi import HTTPException
from instagrapi.exceptions import LoginRequired, ClientError, ClientLoginRequired, RateLimitError

class InstagramHashtagFetcher:
    def __init__(self, client):
        self.client = client

    def get_hashtag_medias(self, hashtag: str, amount: int = 20) -> List[Media]:
        """Get recent posts by hashtag"""
        try:
            medias = self.client.hashtag_medias_recent(name=hashtag, amount=amount)
            return medias
        except LoginRequired:
            print("Session expired or invalid. Need to login again.")
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "error",
                    "code": "LOGIN_REQUIRED",
                    "message": "Instagram session expired. Please login again."
                }
            )
        except ClientLoginRequired:
            print("Client login required")
            raise HTTPException(
                status_code=401,
                detail={
                    "status": "error",
                    "code": "CLIENT_LOGIN_REQUIRED",
                    "message": "Instagram authentication required. Please login first."
                }
            )
        except RateLimitError:
            print("Rate limit reached")
            raise HTTPException(
                status_code=429,
                detail={
                    "status": "error",
                    "code": "RATE_LIMIT",
                    "message": "Too many requests. Please try again later."
                }
            )
        except ClientError as e:
            print(f"Instagram client error: {str(e)}")
            raise HTTPException(
                status_code=400,
                detail={
                    "status": "error",
                    "code": "CLIENT_ERROR",
                    "message": str(e)
                }
            )
        except Exception as e:
            print(f"Unexpected error fetching hashtag medias: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "code": "UNKNOWN_ERROR",
                    "message": "An unexpected error occurred while fetching hashtag data.",
                    "error_details": str(e)
                }
            )

    def get_hashtag_info(self, hashtag: str):
        """해시태그 정보 가져오기"""
        try:
            return self.client.hashtag_info(hashtag)
        except Exception as e:
            print(f"Error fetching hashtag info: {str(e)}")
            raise

    def get_top_posts(self, hashtag: str, amount: int = 9) -> List[Media]:
        """해시태그의 인기 게시물 가져오기"""
        try:
            return self.client.hashtag_medias_top(name=hashtag, amount=amount)
        except Exception as e:
            print(f"Error fetching top posts: {str(e)}")
            raise 