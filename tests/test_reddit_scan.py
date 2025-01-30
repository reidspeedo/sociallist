import requests
import os
from requests.auth import HTTPBasicAuth

def test_reddit_scan():
    # Retrieve username and password from environment variables
    username = os.getenv('API_USERNAME')
    password = os.getenv('API_PASSWORD')
    
    # API endpoint
    url = "http://localhost:8000/reddit/scan"  # For local testing

    # Make a GET request with basic authentication
    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password)
    )

    posts = response.json()
    
    print(f"\nFound {len(posts)} matching posts:")
    for post in posts:
        print(f"\n{post['title']}")
        print(f"r/{post['subreddit']} - {post['url']}")

if __name__ == "__main__":
    test_reddit_scan()