from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SocialPost(BaseModel):
    platform: str
    content: str
    title: Optional[str] = None
    author: str
    url: str
    timestamp: datetime
    keyword_matched: str
    subreddit: Optional[str] = None  # Reddit specific
    score: Optional[int] = None      # Reddit specific
    num_comments: Optional[int] = None  # Reddit specific
    community: Optional[str] = None  # Twitter community
    likes: Optional[int] = None      # Twitter likes
    retweets: Optional[int] = None   # Twitter retweets
    video_id: Optional[str] = None  # YouTube specific  
