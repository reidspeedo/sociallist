from typing import List
import resend
import logging
from datetime import datetime
from ..models.social_post import SocialPost
from ..config.settings import get_settings

logger = logging.getLogger(__name__)

def create_email_content(posts: List[SocialPost]) -> str:
    # Group posts by platform
    platform_posts = {}
    for post in posts:
        if post.platform not in platform_posts:
            platform_posts[post.platform] = []
        platform_posts[post.platform].append(post)

    html_content = f"""
    <h2>Social Listening Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</h2>
    <p>Found {len(posts)} new matching posts across platforms</p>
    """
    
    for platform, platform_posts in platform_posts.items():
        html_content += f"<h3>{platform.title()} - {len(platform_posts)} posts</h3>"
        
        for post in platform_posts:
            html_content += f"""
            <div style="margin-bottom: 20px; padding: 10px; border: 1px solid #ccc;">
            """

            # Title section (Reddit has titles, others use content preview)
            if post.title:
                html_content += f'<h3><a href="{post.url}">{post.title}</a></h3>'
            else:
                preview = post.content[:100] + "..." if len(post.content) > 100 else post.content
                html_content += f'<h3><a href="{post.url}">{preview}</a></h3>'

            # Platform-specific fields
            if platform == "reddit":
                html_content += f"""
                <p><strong>Subreddit:</strong> r/{post.subreddit}</p>
                <p><strong>Author:</strong> u/{post.author}</p>
                <p><strong>Score:</strong> {post.score} | <strong>Comments:</strong> {post.num_comments}</p>
                """
            elif platform == "twitter":
                html_content += f"""
                <p><strong>Author:</strong> @{post.author}</p>
                <p><strong>Likes:</strong> {post.likes} | <strong>Retweets:</strong> {post.retweets}</p>
                """
            elif platform == "bluesky":
                html_content += f"""
                <p><strong>Author:</strong> {post.author}</p>
                <p><strong>Likes:</strong> {post.likes}</p>
                """
            elif platform == "youtube":
                html_content += f"""
                <p><strong>Author:</strong> {post.author}</p>
                <p><strong>Video ID:</strong> {post.video_id}</p>
                <p><strong>Likes:</strong> {post.likes}</p>
                """

            # Common fields for all platforms
            html_content += f"""
                <p><strong>Matched Keyword:</strong> {post.keyword_matched}</p>
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
            "subject": f"Social Listening Report - {len(posts)} new matches across platforms",
            "html": email_content
        }

        response = resend.Emails.send(params)
        logger.info(f"Email notification sent successfully")
        
    except Exception as e:
        logger.error(f"Failed to send email notification: {str(e)}")
        # Don't raise the exception - we don't want the scan to fail if email fails
