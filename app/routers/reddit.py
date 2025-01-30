from fastapi import APIRouter, HTTPException
from ..services.reddit_service import RedditService
from ..services.email_service import send_notification
from ..models.social_post import SocialPost
from typing import List
import logging

router = APIRouter(
    prefix="/reddit",
    tags=["reddit"]
)

logger = logging.getLogger("uvicorn")

@router.get("/scan", response_model=List[SocialPost])
async def scan_subreddits():
    """
    Scan configured subreddits for posts matching keywords
    within the configured time interval
    """
    logger.info("Starting Reddit scan endpoint")
    try:
        reddit_service = RedditService()
        posts = await reddit_service.get_matching_posts()
        
        if posts:
            logger.info(f"Found {len(posts)} matching posts, sending email notification")
            await send_notification(posts)
        else:
            logger.info("No matching posts found")
        
        return posts
    except Exception as e:
        logger.error(f"Reddit scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
