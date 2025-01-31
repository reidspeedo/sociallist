from fastapi import APIRouter, HTTPException
from ..services.bluesky_service import BlueskyService
from ..services.email_service import send_notification
from ..models.social_post import SocialPost
from typing import List
import logging

router = APIRouter(
    prefix="/bluesky",
    tags=["bluesky"]
)

logger = logging.getLogger("uvicorn")

@router.get("/scan", response_model=List[SocialPost])
async def scan_bluesky():
    """
    Scan Bluesky for posts matching keywords
    within the configured time interval
    """
    logger.info("Starting Bluesky scan endpoint")
    try:
        bluesky_service = BlueskyService()
        posts = await bluesky_service.get_matching_posts()
        
        if posts:
            logger.info(f"Found {len(posts)} matching posts, sending email notification")
            await send_notification(posts)
        else:
            logger.info("No matching posts found")
        
        return posts
    except Exception as e:
        logger.error(f"Bluesky scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 