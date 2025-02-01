from fastapi import APIRouter, HTTPException
from ..services.reddit_service import RedditService
from ..services.twitter_service import TwitterService
from ..services.bluesky_service import BlueskyService
from ..services.youtube_service import YouTubeService
from ..services.email_service import send_notification
from ..models.social_post import SocialPost
from typing import List
import logging

router = APIRouter(
    prefix="/aggregate",
    tags=["aggregate"]
)

logger = logging.getLogger("uvicorn")

@router.get("/scan", response_model=List[SocialPost])
async def scan_all():
    """
    Scan all platforms (excluding Instagram) for posts matching keywords
    within the configured time interval
    """
    logger.info("Starting aggregate scan endpoint")
    try:
        reddit_service = RedditService()
        twitter_service = TwitterService()
        bluesky_service = BlueskyService()
        youtube_service = YouTubeService()

        reddit_posts = await reddit_service.get_matching_posts()
        twitter_posts = await twitter_service.get_matching_posts()
        bluesky_posts = await bluesky_service.get_matching_posts()
        youtube_posts = await youtube_service.get_matching_posts()

        all_posts = reddit_posts + twitter_posts + bluesky_posts + youtube_posts

        if all_posts:
            logger.info(f"Found {len(all_posts)} matching posts, sending email notification")
            await send_notification(all_posts)
        else:
            logger.info("No matching posts found")

        return all_posts
    except Exception as e:
        logger.error(f"Aggregate scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 