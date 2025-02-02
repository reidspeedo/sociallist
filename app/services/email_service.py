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
            html_content += """
            <table style="width: 100%; margin-bottom: 15px; border-collapse: collapse; border: 1px solid #e0e0e0;">
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 10px;">
            """
            
            # Add the title/preview as a link
            if post.title:
                html_content += f'<a href="{post.url}" style="text-decoration: none; color: #0066cc; font-weight: bold;">{post.title}</a>'
            else:
                preview = post.content[:100] + "..." if len(post.content) > 100 else post.content
                html_content += f'<a href="{post.url}" style="text-decoration: none; color: #0066cc; font-weight: bold;">{preview}</a>'
            
            html_content += """
                    </td>
                </tr>
                <tr>
                    <td style="padding: 10px;">
            """
            
            # Only show content preview and matched keyword
            html_content += f"""
                <p><strong>Matched Keyword:</strong> {post.keyword_matched}</p>
                <p><strong>Content Preview:</strong> {post.content[:200]}...</p>
            """
            
            html_content += """
                    </td>
                </tr>
            </table>
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
