from pydantic_settings import BaseSettings
from functools import lru_cache
import yaml
from pathlib import Path

class Settings(BaseSettings):
    # Reddit Configuration
    REDDIT_CLIENT_ID: str
    REDDIT_CLIENT_SECRET: str
    REDDIT_USER_AGENT: str
    
    # Resend Email Configuration
    RESEND_API_KEY: str
    EMAIL_FROM: str
    EMAIL_TO: str
    
    # Scan Configuration
    SCAN_INTERVAL_MINUTES: int
    
    # API Authentication
    API_USERNAME: str
    API_PASSWORD: str
    
    # Twitter Configuration
    TWITTER_USERNAME: str
    TWITTER_PASSWORD: str
    TWITTER_EMAIL: str
    
    # Bluesky Configuration
    BLUESKY_EMAIL: str
    BLUESKY_PASSWORD: str 

    # Youtube Configuration
    YOUTUBE_API_KEY: str
    
    # Instagram Configuration
    INSTAGRAM_USERNAME: str
    INSTAGRAM_PASSWORD: str
    INSTAGRAM_EMAIL: str
    INSTAGRAM_EMAIL_PASSWORD: str
    
    # OpenAI Configuration
    OPENAI_API_KEY: str
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

@lru_cache()
def get_keywords():
    keywords_path = Path(__file__).parent / "keywords.yml"
    with open(keywords_path, 'r') as file:
        return yaml.safe_load(file)
