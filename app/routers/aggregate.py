from fastapi import APIRouter, HTTPException
from ..services.reddit_service import RedditService
from ..services.twitter_service import TwitterService
from ..services.bluesky_service import BlueskyService
from ..services.youtube_service import YouTubeService
from ..services.email_service import send_notification
from ..models.social_post import SocialPost
from typing import List
import logging
from ..services.openai_service import OpenAIService

router = APIRouter(
    prefix="/aggregate",
    tags=["aggregate"]
)

logger = logging.getLogger("uvicorn")

@router.get("/scan", response_model=List[SocialPost])
async def scan_all(apply_ai_filter: bool = False):
    """
    Scan all platforms (excluding Instagram) for posts matching keywords
    within the configured time interval.
    
    Parameters:
        apply_ai_filter (bool): Whether to apply OpenAI filtering (default: True)
    """
    logger.info("Starting aggregate scan endpoint")
    try:
        # Get initial matches from all services
        reddit_service = RedditService()
        # twitter_service = TwitterService()
        bluesky_service = BlueskyService()
        youtube_service = YouTubeService()

        # Collect all initial matches
        all_posts = (
            await reddit_service.get_matching_posts() +
            # await twitter_service.get_matching_posts() +
            await bluesky_service.get_matching_posts() +
            await youtube_service.get_matching_posts()
        )
        
        if all_posts:
            logger.info(f"Found {len(all_posts)} initial matches")
            
            if apply_ai_filter:
                # Apply OpenAI filter
                openai_service = OpenAIService()
                filtered_posts = await openai_service.filter_promotion_worthy(all_posts)
                
                if filtered_posts:
                    logger.info(f"After AI filtering: {len(filtered_posts)} promotion-worthy posts")
                    await send_notification(filtered_posts)
                else:
                    logger.info("No posts passed AI filtering")
                    
                return filtered_posts
            else:
                logger.info("Skipping AI filtering as requested")
                await send_notification(all_posts)
                return all_posts
        else:
            logger.info("No initial matches found")
            return []
            
    except Exception as e:
        logger.error(f"Aggregate scan failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 