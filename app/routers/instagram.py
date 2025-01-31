from fastapi import APIRouter, HTTPException
from ..services.instagram_service import InstagramService
from ..services.email_service import send_notification
from ..models.social_post import SocialPost
from typing import List
import logging

router = APIRouter(
    prefix="/instagram",
    tags=["instagram"]
)

logger = logging.getLogger("uvicorn")

@router.get("/scan", response_model=List[SocialPost])
async def scan_instagram():
    """
    Scan configured Instagram accounts for comments matching keywords
    within the configured time interval
    """
    logger.info("Starting Instagram scan endpoint")
    try:
        instagram_service = InstagramService()
        posts = await instagram_service.get_matching_posts()
        
        if posts:
            logger.info(f"Found {len(posts)} matching posts, sending email notification")
            await send_notification(posts)
        else:
            logger.info("No matching posts found")
        
        return posts
    except Exception as e:
        logger.error(f"Instagram scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 