from typing import List
import resend
import logging
from datetime import datetime
from ..models.social_post import SocialPost
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

def create_email_content(posts: List[SocialPost]) -> str:
    html_content = f"""
    <h2>Social Listening Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
    <p>Found {len(posts)} new matching posts on Reddit:</p>
    """
    
    for post in posts:
        html_content += f"""
        <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ccc;">
            <h3><a href="{post.url}">{post.title}</a></h3>
            <p><strong>Subreddit:</strong> r/{post.subreddit}</p>
            <p><strong>Author:</strong> u/{post.author}</p>
            <p><strong>Matched Keyword:</strong> {post.keyword_matched}</p>
            <p><strong>Score:</strong> {post.score} | <strong>Comments:</strong> {post.num_comments}</p>
            <p><strong>Content Preview:</strong> {post.content[:200]}...</p>
            <p><strong>Posted:</strong> {post.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
        </div>
        """
    
    return html_content

async def send_notification(posts: List[SocialPost]):
    settings = get_settings()
    resend.api_key = settings.RESEND_API_KEY
    
    try:
        email_content = create_email_content(posts)
        
        params = {
            "from": settings.EMAIL_FROM,
            "to": [settings.EMAIL_TO],
            "subject": f"Social Listening Report - {len(posts)} new Reddit matches",
            "html": email_content
        }

        response = resend.Emails.send(params)
        logger.info(f"Email notification sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        # Don't raise the exception - we don't want the scan to fail if email fails
