from fastapi import APIRouter, HTTPException
from ..services.twitter_service import TwitterService
from ..services.email_service import send_notification
from ..models.social_post import SocialPost
from typing import List
import logging

router = APIRouter(
    prefix="/twitter",
    tags=["twitter"]
)

logger = logging.getLogger("uvicorn")

@router.get("/communities", response_model=List[SocialPost])
async def scan_communities():
    """
    Scan configured Twitter communities for posts matching keywords
    within the configured time interval
    """
    logger.info("Starting Twitter communities scan endpoint")
    try:
        twitter_service = TwitterService()
        posts = await twitter_service.get_matching_posts()
        
        if posts:
            logger.info(f"Found {len(posts)} matching posts, sending email notification")
            await send_notification(posts)
        else:
            logger.info("No matching posts found")
        
        return posts
    except Exception as e:
        logger.error(f"Twitter scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 