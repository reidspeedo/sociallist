from atproto import Client
from datetime import datetime, timedelta, timezone
from ..models.social_post import SocialPost
from ..config.settings import get_settings, get_keywords
from .matchers.base_matcher import BaseMatcher
from .matchers.question_matcher import QuestionMatcher
from typing import List
import logging

logger = logging.getLogger("uvicorn")

class BlueskyService:
    def __init__(self):
        self.settings = get_settings()
        self.keywords = get_keywords()["bluesky"]
        self.client = self._initialize_bluesky()

    def _initialize_bluesky(self):
        try:
            client = Client()
            client.login(
                self.settings.BLUESKY_EMAIL,
                self.settings.BLUESKY_PASSWORD
            )
            logger.info("Successfully initialized Bluesky API client")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Bluesky client: {str(e)}")
            raise

    def _normalize_post(self, post, matched_keyword: str) -> SocialPost:
        """Convert Bluesky post to normalized SocialPost model"""
        return SocialPost(
            platform="bluesky",
            content=post.record.text,
            title=None,
            author=post.author.handle,
            url=f"https://bsky.app/profile/{post.author.handle}/post/{post.uri.split('/')[-1]}",
            timestamp=datetime.fromisoformat(post.indexed_at.replace('Z', '+00:00')),
            keyword_matched=matched_keyword,
            community=None,
            likes=getattr(post, 'like_count', 0),
            retweets=getattr(post, 'repost_count', 0)
        )

    async def get_matching_posts(self) -> List[SocialPost]:
        """Get posts matching configured keywords from configured feeds"""
        matching_posts = []
        scan_cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=self.settings.SCAN_INTERVAL_MINUTES)
        logger.info(f"Starting Bluesky scan, cutoff time: {scan_cutoff}")

        try:
            for feed_config in self.keywords["feeds"]:
                try:
                    # Split the feed config into handle and feed ID
                    handle, feed_id = feed_config.split('/')
                    logger.info(f"Getting feed for handle: {handle}, feed_id: {feed_id}")

                    # Get the DID from the handle
                    profile = self.client.app.bsky.actor.get_profile({'actor': handle})
                    feed_uri = f"at://{profile.did}/app.bsky.feed.generator/{feed_id}"
                    logger.info(f"Using feed URI: {feed_uri}")

                    response = self.client.app.bsky.feed.get_feed({
                        'feed': feed_uri,
                        'limit': 100
                    })
                    
                    if not response.feed:
                        logger.info(f"No posts found in feed {feed_uri}")
                        continue

                    for feed_view in response.feed:
                        post = feed_view.post
                        post_time = datetime.fromisoformat(post.indexed_at.replace('Z', '+00:00'))
                        
                        if post_time < scan_cutoff:
                            continue


                        matches, keyword = self._match_content(post.record.text)
                        
                        if matches:
                            matching_posts.append(
                                self._normalize_post(post, keyword)
                            )
                            logger.info(f"Found matching post with keyword '{keyword}'")

                except Exception as e:
                    logger.error(f"Error fetching feed {feed_config}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in Bluesky scan: {str(e)}")
            raise

        logger.info(f"Scan complete. Found {len(matching_posts)} total matching posts")
        return matching_posts

    def _match_content(self, text: str) -> tuple[bool, str]:
        """Match content against keywords and patterns"""
        # Try base keyword matching first
        matches, keyword = BaseMatcher.match(text, self.keywords)
        if matches:
            logger.info(f"Found matching keyword: {keyword}")
            return True, keyword
        
        # Try question matching
        matches, pattern = QuestionMatcher.match(text, self.keywords)
        if matches:
            logger.info(f"Found matching question pattern: {pattern}")
            return True, pattern
        
        return False, "" 