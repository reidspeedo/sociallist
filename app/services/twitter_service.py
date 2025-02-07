from twikit import Client
from datetime import datetime, timedelta, timezone
from ..models.social_post import SocialPost
from ..config.settings import get_settings, get_keywords
from .matchers.base_matcher import BaseMatcher
from .matchers.question_matcher import QuestionMatcher
from typing import List, Tuple
import logging
from asyncio import sleep
import random
import os
import json

logger = logging.getLogger("uvicorn")

class TwitterService:
    def __init__(self):
        self.settings = get_settings()
        self.keywords = get_keywords()["twitter"]
        self.max_tweets = random.randint(90, 100)  # Randomize max tweets per community
        self.client = None  # Initialize as None, will be set later

    async def _initialize_twitter(self):
        max_retries = 3
        retry_delay = 60  # seconds
        cookies_file = "cookies.json"
        # Instead of a fixed threshold, choose a random threshold between 2 and 4 days
        random_days = random.uniform(2, 4)
        cookies_age_limit = timedelta(days=random_days)
        logger.info(f"Using a cookies refresh threshold of {random_days:.2f} days")

        for attempt in range(max_retries):
            try:
                client = Client(language='en-US')

                # Check if cookies exist and are still within the randomized valid window
                if os.path.exists(cookies_file):
                    with open(cookies_file, 'r') as f:
                        cookies_data = json.load(f)
                        last_refreshed = datetime.fromisoformat(
                            cookies_data.get('last_refreshed', '1970-01-01T00:00:00')
                        )
                    
                    if datetime.now() - last_refreshed < cookies_age_limit:
                        client.load_cookies(cookies_file)
                        logger.info("Loaded saved cookies, skipping login")
                        return client

                # Perform login and save cookies with a timestamp
                await client.login(
                    auth_info_1=self.settings.TWITTER_USERNAME,
                    auth_info_2=self.settings.TWITTER_EMAIL,
                    password=self.settings.TWITTER_PASSWORD
                )
                client.save_cookies(cookies_file)

                # Update cookies file with a new timestamp
                with open(cookies_file, 'r+') as f:
                    cookies_data = json.load(f)
                    cookies_data['last_refreshed'] = datetime.now().isoformat()
                    f.seek(0)
                    json.dump(cookies_data, f)
                    f.truncate()

                logger.info("Logged in and saved cookies")
                return client
            except Exception as e:
                # If blocked, retry with exponential backoff
                if "blocked" in str(e).lower():
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        logger.warning(f"Twitter login blocked, waiting {wait_time}s before retry {attempt + 1}/{max_retries}")
                        await sleep(wait_time)
                        continue
                logger.error("Failed to initialize Twitter client")
                raise

    async def ensure_client(self):
        if self.client is None:
            self.client = await self._initialize_twitter()

    def _match_content(self, text: str) -> Tuple[bool, str]:
        """Match content against keywords and patterns"""
        matches, keyword = BaseMatcher.match(text, self.keywords)
        if matches:
            logger.info(f"Found matching keyword: {keyword}")
            return True, keyword
        
        matches, pattern = QuestionMatcher.match(text, self.keywords)
        if matches:
            logger.info(f"Found matching question pattern: {pattern}")
            return True, pattern
        
        return False, ""

    async def get_matching_posts(self) -> List[SocialPost]:
        """Get posts from configured communities matching keywords"""
        # Add a random delay (2-5 minutes) before starting the service to mimic a non-automated behavior.
        random_delay = random.uniform(120, 300)
        logger.info(f"Waiting for {random_delay:.2f} seconds before starting Twitter service")
        await sleep(random_delay)

        await self.ensure_client()
        try:
            matching_posts = []
            scan_cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=self.settings.SCAN_INTERVAL_MINUTES)
            
            communities = list(self.keywords.get("communities", []))
            random.shuffle(communities)
            
            for community_id in communities:
                try:
                    # Random delay between communities (2-5 seconds)
                    await sleep(random.uniform(60, 120))
                    
                    # Randomize tweet count for this community
                    tweet_count = random.randint(30, self.max_tweets)
                    logger.info(f"Fetching {tweet_count} tweets from community {community_id}")
                    
                    tweets = await self.client.get_community_tweets(
                        community_id=community_id,
                        tweet_type='Latest',
                        count=tweet_count
                    )
                    
                    # Convert to list and randomize processing order
                    tweets_list = list(tweets)
                    random.shuffle(tweets_list)
                    
                    for tweet in tweets_list:
                        # Random delay between tweet processing (0.5-2 seconds)
                        await sleep(random.uniform(0.5, 2))
                        
                        # Ensure tweet time is timezone-aware
                        tweet_time = tweet.created_at_datetime
                        if tweet_time.tzinfo is None:
                            tweet_time = tweet_time.replace(tzinfo=timezone.utc)
                        
                        if tweet_time < scan_cutoff:
                            continue
                        
                        matches, keyword = self._match_content(tweet.text)
                        if matches:
                            logger.info(f"Match found for tweet: {tweet.text} with keyword: {keyword}")
                            matching_posts.append(SocialPost(
                                platform="twitter",
                                content=tweet.text,
                                url=f"https://twitter.com/i/web/status/{tweet.id}",
                                timestamp=tweet_time,
                                author=tweet.user.screen_name,
                                community=community_id,
                                keyword_matched=keyword
                            ))
                            
                            # Random delay after finding a match (1-3 seconds)
                            await sleep(random.uniform(1, 3))
                    
                except Exception as e:
                    logger.error(f"Error processing community {community_id}: {str(e)}")
                    await sleep(random.uniform(5, 10))
                    continue

            logger.info(f"Found {len(matching_posts)} matching Twitter posts")
            return matching_posts

        except Exception as e:
            logger.error(f"Failed to get matching Twitter posts: {str(e)}")
            raise 