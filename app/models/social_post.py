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
