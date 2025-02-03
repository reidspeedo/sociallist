from googleapiclient.discovery import build
from datetime import datetime, timedelta, timezone
from ..models.social_post import SocialPost
from ..config.settings import get_settings, get_keywords
from .matchers.base_matcher import BaseMatcher
from typing import List, Tuple
import logging
import asyncio
from googleapiclient.errors import HttpError

logger = logging.getLogger("uvicorn")

class YouTubeService:
    def __init__(self):
        logger.info("Initializing YouTubeService")
        self.settings = get_settings()
        self.keywords = get_keywords()["youtube"]
        self.youtube = self._initialize_youtube()

    def _initialize_youtube(self):
        try:
            youtube = build('youtube', 'v3', developerKey=self.settings.YOUTUBE_API_KEY)
            return youtube
        except Exception as e:
            logger.error(f"Failed to initialize YouTube client: {str(e)}")
            raise

    def _normalize_post(self, comment, video_id, video_title, matched_keyword: str) -> SocialPost:
        """Convert YouTube comment to normalized SocialPost model"""
        return SocialPost(
            platform="youtube",
            content=comment['snippet']['textDisplay'],
            title=video_title,
            author=comment['snippet']['authorDisplayName'],
            url=f"https://youtube.com/watch?v={video_id}&lc={comment['id']}",
            timestamp=datetime.fromisoformat(comment['snippet']['publishedAt'].replace('Z', '+00:00')),
            keyword_matched=matched_keyword,
            community=None,
            likes=comment['snippet'].get('likeCount', 0),
            video_id=video_id
        )

    async def get_matching_posts(self) -> List[SocialPost]:
        """Get comments created in the last X minutes matching configured keywords"""
        matching_posts = []
        scan_cutoff = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(minutes=self.settings.SCAN_INTERVAL_MINUTES)
        logger.info(f"Starting YouTube scan, cutoff time: {scan_cutoff}")

        try:
            for channel_id in self.keywords["channels"]:
                try:
                    # Get videos from channel
                    videos_response = self.youtube.search().list(
                        channelId=channel_id,
                        order="date",
                        part="snippet",
                        maxResults=5,
                        type="video"
                    ).execute()

                    videos = videos_response.get("items", [])
                    video_details = [
                        (video["id"]["videoId"], video["snippet"]["title"])
                        for video in videos
                    ]

                    for video_id, video_title in video_details:
                        try:
                            next_page_token = None
                            comments_to_process = True

                            while comments_to_process:
                                try:
                                    comments_response = self.youtube.commentThreads().list(
                                        part="snippet",
                                        videoId=video_id,
                                        maxResults=100,
                                        order="time",
                                        pageToken=next_page_token
                                    ).execute()
                                except HttpError as e:
                                    if "commentsDisabled" in str(e):
                                        logger.info(f"Skipping video {video_id} - comments are disabled")
                                        break
                                    raise

                                comments = comments_response.get("items", [])

                                for comment_thread in comments:
                                    comment = comment_thread["snippet"]["topLevelComment"]
                                    comment_time = datetime.fromisoformat(
                                        comment["snippet"]["publishedAt"].replace('Z', '+00:00')
                                    )
                                    
                                    if comment_time < scan_cutoff:
                                        comments_to_process = False
                                        break

                                    matches, keyword = BaseMatcher.match(
                                        comment["snippet"]["textDisplay"], 
                                        self.keywords
                                    )
                                    
                                    if matches:
                                        matching_posts.append(
                                            self._normalize_post(comment, video_id, video_title, keyword)
                                        )

                                if not comments_to_process or "nextPageToken" not in comments_response:
                                    comments_to_process = False
                                else:
                                    next_page_token = comments_response["nextPageToken"]
                                    await asyncio.sleep(0.1)

                        except Exception as e:
                            logger.error(f"Error processing video {video_id}: {str(e)}")
                            continue

                except Exception as e:
                    logger.error(f"Error scanning channel {channel_id}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error in YouTube scan: {str(e)}")
            raise

        logger.info(f"YouTube scan complete. Found {len(matching_posts)} matching posts")
        return matching_posts

    def _match_content(self, text: str) -> Tuple[bool, str]:
        """Check if text matches any configured keywords"""
        text = text.lower()
        
        # Log the text being checked and the keywords
        logger.debug(f"Checking text against keywords: {self.keywords['keywords']}")
        logger.debug(f"Text: {text[:100]}...")  # First 100 chars

        # Check excluded keywords first
        for excl in self.keywords.get("exclude_keywords", []):
            if excl.lower() in text:
                logger.debug(f"Text excluded due to keyword: {excl}")
                return False, ""

        # Check included keywords
        for keyword in self.keywords["keywords"]:
            if keyword.lower() in text:
                logger.debug(f"Found matching keyword: {keyword}")
                return True, keyword

        return False, "" 