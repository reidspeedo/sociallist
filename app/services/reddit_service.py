import asyncpraw
import ssl
import certifi
from aiohttp import ClientSession, TCPConnector
from ..models.social_post import SocialPost
from ..config.settings import get_settings, get_keywords
from .matchers.base_matcher import BaseMatcher
from .matchers.question_matcher import QuestionMatcher
from datetime import datetime, timedelta
from typing import List
import logging
import re

logger = logging.getLogger("uvicorn")

class RedditService:
    def __init__(self):
        logger.info("Initializing RedditService")
        self.settings = get_settings()
        self.keywords = get_keywords()["reddit"]
        self.reddit = self._initialize_reddit()
        logger.info(f"Configured to scan subreddits: {', '.join(self.keywords['subreddits'])}")

    def _initialize_reddit(self):
        """Initialize Reddit API client with proper SSL context"""
        try:
            # Create SSL context with certifi certificates
            ssl_context = ssl.create_default_context(cafile=certifi.where())
            
            # Create connector with SSL context
            connector = TCPConnector(ssl=ssl_context)
            
            # Create session with connector
            session = ClientSession(connector=connector, trust_env=True)
            
            reddit = asyncpraw.Reddit(
                client_id=self.settings.REDDIT_CLIENT_ID,
                client_secret=self.settings.REDDIT_CLIENT_SECRET,
                user_agent=self.settings.REDDIT_USER_AGENT,
                requestor_kwargs={'session': session}
            )
            logger.info("Successfully initialized Reddit API client")
            return reddit
            
        except Exception as e:
            logger.error(f"Failed to initialize Reddit client: {str(e)}")
            raise

    def _check_reddit_specific_patterns(self, text: str) -> tuple[bool, str]:
        """Reddit-specific pattern matching"""
        question_patterns = [
            r"(?i)how (do|can|should) (i|you|one)",
            r"(?i)what('s| is) (the best|a good)",
            r"(?i)anyone know (of|about|how)",
        ]
        
        for pattern in question_patterns:
            if re.search(pattern, text):
                return True, f"question_pattern:{pattern}"
        
        return False, ""

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

    def _normalize_post(self, submission, matched_keyword: str) -> SocialPost:
        """Convert Reddit submission to normalized SocialPost model"""
        return SocialPost(
            platform="reddit",
            content=submission.selftext,
            title=submission.title,
            author=str(submission.author),
            url=f"https://reddit.com{submission.permalink}",
            timestamp=datetime.fromtimestamp(submission.created_utc),
            keyword_matched=matched_keyword,
            subreddit=str(submission.subreddit),
            score=submission.score,
            num_comments=submission.num_comments
        )

    async def get_matching_posts(self) -> List[SocialPost]:
        """Get posts matching configured keywords from configured subreddits"""
        matching_posts = []
        scan_cutoff = datetime.utcnow() - timedelta(minutes=self.settings.SCAN_INTERVAL_MINUTES)
        logger.info(f"Starting Reddit scan, cutoff time: {scan_cutoff}")

        try:
            for subreddit_name in self.keywords["subreddits"]:
                try:
                    logger.info(f"Scanning r/{subreddit_name}")
                    subreddit = await self.reddit.subreddit(subreddit_name)
                    posts_checked = 0
                    
                    async for submission in subreddit.new(limit=500):
                        posts_checked += 1
                        post_time = datetime.fromtimestamp(submission.created_utc)
                        if post_time < scan_cutoff:
                            logger.info(f"Reached cutoff time in r/{subreddit_name} after checking {posts_checked} posts")
                            break

                        post_text = f"{submission.title} {submission.selftext}"
                        matches, keyword = self._match_content(post_text)
                        
                        logger.debug(f"Post {posts_checked}: Match={matches}, Keyword={keyword}, Title={submission.title[:50]}...")
                        
                        if matches:
                            matching_posts.append(
                                self._normalize_post(submission, keyword)
                            )

                    logger.info(f"Completed scanning r/{subreddit_name}, checked {posts_checked} posts, found {len(matching_posts)} matches")
                    
                except Exception as e:
                    logger.error(f"Error scanning r/{subreddit_name}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in Reddit scan: {str(e)}")
            raise

        logger.info(f"Scan complete. Found {len(matching_posts)} total matching posts")
        return matching_posts

    async def close(self):
        """Close the Reddit client session"""
        try:
            await self.reddit.close()
            logger.info("Closed Reddit client session")
        except Exception as e:
            logger.error(f"Error closing Reddit client: {str(e)}") 