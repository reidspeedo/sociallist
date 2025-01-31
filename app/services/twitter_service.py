import tweepy
from datetime import datetime, timedelta
from ..models.social_post import SocialPost
from ..config.settings import get_settings, get_keywords
from .matchers.base_matcher import BaseMatcher
from typing import List
import logging
import asyncio

logger = logging.getLogger("uvicorn")

class TwitterService:
    def __init__(self):
        logger.info("Initializing TwitterService")
        self.settings = get_settings()
        self.keywords = get_keywords()["twitter"]
        self.client = self._initialize_twitter()
        logger.info(f"Configured to search keywords: {', '.join(self.keywords['search_terms'])}")

    def _initialize_twitter(self):
        try:
            client = tweepy.Client(
                bearer_token=self.settings.TWITTER_BEARER_TOKEN,
                consumer_key=self.settings.TWITTER_API_KEY,
                consumer_secret=self.settings.TWITTER_API_SECRET,
                access_token=self.settings.TWITTER_ACCESS_TOKEN,
                access_token_secret=self.settings.TWITTER_ACCESS_SECRET
            )
            logger.info("Successfully initialized Twitter API client")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Twitter client: {str(e)}")
            raise

    def _normalize_post(self, tweet, matched_keyword: str) -> SocialPost:
        """Convert Twitter post to normalized SocialPost model"""
        return SocialPost(
            platform="twitter",
            content=tweet.text,
            title=None,  # Twitter doesn't have titles
            author=str(tweet.author_id),  # Convert author_id to string
            url=f"https://twitter.com/user/status/{tweet.id}",
            timestamp=tweet.created_at,
            keyword_matched=matched_keyword,
            community=None,
            likes=tweet.public_metrics['like_count'] if hasattr(tweet, 'public_metrics') else None,
            retweets=tweet.public_metrics['retweet_count'] if hasattr(tweet, 'public_metrics') else None
        )

    async def get_matching_posts(self) -> List[SocialPost]:
        """Get posts matching configured keywords"""
        matching_posts = []
        scan_cutoff = datetime.utcnow() - timedelta(minutes=self.settings.SCAN_INTERVAL_MINUTES)
        logger.info(f"Starting Twitter scan, cutoff time: {scan_cutoff}")

        try:
            for search_term in self.keywords["search_terms"]:
                try:
                    logger.info(f"Searching for term: {search_term}")
                    
                    # Add delay between requests to avoid rate limits
                    await asyncio.sleep(1)  # 1 second delay between requests
                    
                    response = self.client.search_recent_tweets(
                        query=f"{search_term} -is:retweet",
                        max_results=10,  # Reduced from 100 to avoid hitting limits
                        start_time=scan_cutoff,
                        tweet_fields=['created_at', 'public_metrics', 'text', 'author_id']
                    )
                    
                    if not response.data:
                        continue

                    for tweet in response.data:
                        matching_posts.append(
                            self._normalize_post(tweet, search_term)
                        )

                    logger.info(f"Completed searching term {search_term}, found {len(matching_posts)} matches")

                except tweepy.TooManyRequests:
                    logger.warning(f"Rate limit reached for term {search_term}, waiting 15 minutes")
                    await asyncio.sleep(900)  # Wait 15 minutes
                    continue
                except Exception as e:
                    logger.error(f"Error searching term {search_term}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in Twitter scan: {str(e)}")
            raise

        logger.info(f"Scan complete. Found {len(matching_posts)} total matching posts")
        return matching_posts 