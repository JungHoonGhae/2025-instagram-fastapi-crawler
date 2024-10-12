from datetime import datetime

from instagrapi import Client
from instagrapi.exceptions import (
    ChallengeRequired,
    FeedbackRequired,
    LoginRequired,
    PleaseWaitFewMinutes,
    RecaptchaChallengeForm,
    SelectContactPointRecoveryForm,
)
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.database import SessionLocal
from app.models import InstagramPosts, get_best_session

db = SessionLocal()


def get_or_create_insta_post(db: Session, profile_username: str, session_obj):
    # تلاش برای یافتن رکورد
    insta_post = (
        db.query(InstagramPosts)
        .filter_by(profile=profile_username, session=session_obj)
        .first()
    )

    if not insta_post:
        # اگر پیدا نشد، رکورد جدید ایجاد می‌کنیم
        loading_time = str(datetime.now())  # تنظیم مقدار loading_time به زمان فعلی
        insta_post = InstagramPosts(
            profile=profile_username,
            session=session_obj,
            loading_time=loading_time,  # اضافه کردن loading_time
        )
        db.add(insta_post)
        db.commit()
        db.refresh(insta_post)
        created = True
    else:
        created = False

    return insta_post, created


class InstagramDataFetcher:
    print("start fetch_instagram_data")

    def __init__(self, db=db, proxy_ip="http://170.64.207.199", proxy_port="3128"):
        self.db = db
        self.session = self.session = get_best_session(self.db)
        if not self.session:
            raise ValueError("No available session found")

        self.set_proxy = f"{proxy_ip}:{proxy_port}"

        self.client = Client()
        self.client.set_proxy(self.set_proxy)
        self.client.set_settings(self.session.session_data)
        self.client.delay_range = [1, 50]
        self.logged_in = False
        self.login()

    def login(self):
        print("-------------------login")
        USERNAME = self.session.username
        PASSWORD = self.session.password
        try:
            self.client.login(USERNAME, PASSWORD)
            self.logged_in = True
            try:
                self.client.get_timeline_feed()
            except LoginRequired:
                print("Session is invalid, need to login via username and password")
                old_session = self.client.get_settings()

                self.client.set_settings({})
                self.client.set_uuids(old_session["uuids"])

                self.client.login(USERNAME, PASSWORD)
            # login_via_session = True
        except Exception as e:

            # If Login Required
            if isinstance(e, LoginRequired):
                print("LoginRequired")
                self.client.logger.exception(e)
                self.client.relogin()
                self.session.hit_challenge()
                self.session = get_best_session(self.db)
                self.client.set_settings(self.session.session_data)
                self.login()

            # If We Hit The Challenge
            elif isinstance(e, ChallengeRequired):
                print("ChallengeRequired")
                try:
                    self.client.challenge_resolve(self.client.last_json)
                except ChallengeRequired as e:
                    content = f"Challenge Required: {e}"
                except (
                    ChallengeRequired,
                    SelectContactPointRecoveryForm,
                    RecaptchaChallengeForm,
                ) as e:
                    content = f"Challenge, Recaptcha Required: {e}"

                self.session.hit_challenge()
                self.session = get_best_session(self.db)
                self.client.set_settings(self.session.session_data)
                self.login()

            # If We Need To Send Feed Back
            elif isinstance(e, FeedbackRequired):
                print("FeedbackRequired")

                message = self.client.last_json["feedback_message"]
                if "This action was blocked. Please try again later" in message:
                    content = f"Action Blocked, Freeze For 12 Hour: {e}"

                elif "We restrict certain activity to protect our community" in message:
                    # 6 hours is not enough
                    content = f"Action Blocked 2, Freeze For 12 Hour: {e}"

                elif "Your account has been temporarily blocked" in message:
                    """
                    Based on previous use of this feature, your account has been temporarily
                    blocked from taking this action.
                    This block will expire on 2020-03-27.
                    """
                    content = f"Action Blocked: {e}"
                self.session.temp_block()
                self.session = get_best_session(self.db)
                self.client.set_settings(self.session.session_data)
                self.login()

            # If Need To Wait Few Minutes
            elif isinstance(e, PleaseWaitFewMinutes):
                print("PleaseWaitFewMinutes")
                self.session.temp_block()
                self.session = get_best_session(self.db)
                self.client.set_settings(self.session.session_data)
                self.login()

            # We Blocked
            else:
                print("We Blocked")
                self.session.block()
                self.session = get_best_session(self.db)
                self.client.set_settings(self.session.session_data)
                self.login()

    def fetch_posts(self, profile_username):

        print(f"--------------------------starting fetch_posts: {profile_username}")
        try:
            if self.logged_in:
                profile_info = self.client.user_info_by_username(profile_username)
                user_id = self.client.user_id_from_username(profile_username)
                medias_count = profile_info.media_count
                print(f"medias_count:{medias_count}")

                # notify the session used once again
                self.session.increment_use(db)

                end_cursor = None
                all_posts = []
                item_per_page = 20
                while medias_count > 0:
                    medias, end_cursor = self.client.user_medias_paginated(
                        user_id, item_per_page, end_cursor=end_cursor
                    )
                    counter = 1
                    for post in medias:
                        print(f"{counter}_______{post.caption_text[:10]}")
                        current_post = {
                            "caption": post.caption_text,
                            "likes": post.like_count,
                            "comments": post.comment_count,
                            "reels": str(post.video_url),
                            "type": post.media_type,
                            "imgs": [
                                {
                                    "thumbnail_url": str(
                                        resource.thumbnail_url
                                        if resource.media_type == 1
                                        else resource.video_url
                                    ),
                                    "video_url": str(resource.video_url),
                                }
                                for resource in post.resources
                            ],
                        }
                        all_posts.append(current_post)
                    medias_count -= item_per_page

                    insta_post, created = get_or_create_insta_post(
                        self.db, profile_username, self.session
                    )
                    if created:
                        print(f"New post created for profile: {profile_username}")
                    else:
                        print(f"Post already exists for profile: {profile_username}")

                        if created:
                            # اگر پست جدید ایجاد شد
                            insta_post.fill_object(
                                session=self.session, json_posts=all_posts
                            )
                            print(f"New post created for profile: {profile_username}")
                        else:
                            print("else")
                            # دریافت json قدیمی
                            print(type(insta_post.json_posts))
                            existing_json_data = insta_post.json_posts or []

                            print(f"step 1 {existing_json_data}")
                            # اضافه کردن json جدید به داده‌های قبلی
                            existing_json_data.append(all_posts)

                            # به‌روزرسانی json پست
                            insta_post.json_posts = existing_json_data[-1]  # آخرین json
                            print(
                                "/////////////////////////",
                                insta_post,
                                "/////////////////////////",
                            )
                            self.db.add(insta_post)
                            self.db.commit()
                            self.db.refresh(insta_post)  # به‌روزرسانی شیء پس از commit

                            print(f"Post updated for profile: {profile_username}")

                return True
            else:
                print("------------------------------logged_in else")
                return False
        except Exception as e:
            print(str(e))
            return False


async def fetch_instagram_data(profile_username: str):
    print("fetch_instagram_data----------------------")
    insta_data_fetcher = InstagramDataFetcher()

    await run_in_threadpool(insta_data_fetcher.fetch_posts, profile_username)
    # asyncio.run(insta_data_fetcher.fetch_posts(profile_username))
