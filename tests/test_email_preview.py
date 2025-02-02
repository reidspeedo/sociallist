from datetime import datetime, timezone
from app.models.social_post import SocialPost
from app.services.email_service import create_email_content

def create_sample_posts():
    return [
        SocialPost(
            platform="bluesky",
            title="#buildinpublic Day 55",
            content="Looking for a good problem to solve? It exists, but you won't find it doomscrolling...",
            url="https://example.com/1",
            author="rough.app",
            likes=3,
            keyword_matched="problem",
            timestamp=datetime(2025, 2, 2, 18, 12, 28, tzinfo=timezone.utc)
        ),
        SocialPost(
            platform="reddit",
            title="New Project Launch",
            content="Just launched my new project on Product Hunt!",
            url="https://example.com/2",
            author="testuser",
            subreddit="programming",
            score=42,
            num_comments=7,
            keyword_matched="launch",
            timestamp=datetime(2025, 2, 2, 18, 0, 0, tzinfo=timezone.utc)
        ),
        # Add more sample posts as needed
    ]

def test_email_preview():
    posts = create_sample_posts()
    html_content = create_email_content(posts)
    
    # Save the HTML to a file
    with open("email_preview.html", "w") as f:
        f.write(html_content)
    
    print("Preview saved to email_preview.html")

if __name__ == "__main__":
    test_email_preview() 