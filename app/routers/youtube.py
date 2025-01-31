from fastapi import APIRouter, HTTPException
from ..services.youtube_service import YouTubeService
from ..services.email_service import send_notification
from ..models.social_post import SocialPost
from typing import List
import logging

router = APIRouter(
    prefix="/youtube",
    tags=["youtube"]
)

logger = logging.getLogger("uvicorn")

@router.get("/scan", response_model=List[SocialPost])
async def scan_youtube():
    """
    Scan configured YouTube channels for comments matching keywords
    within the configured time interval
    """
    logger.info("Starting YouTube scan endpoint")
    try:
        youtube_service = YouTubeService()
        posts = await youtube_service.get_matching_posts()
        
        if posts:
            logger.info(f"Found {len(posts)} matching posts, sending email notification")
            await send_notification(posts)
        else:
            logger.info("No matching posts found")
        
        return posts
    except Exception as e:
        logger.error(f"YouTube scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 