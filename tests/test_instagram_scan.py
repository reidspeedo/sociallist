import requests
import os
from requests.auth import HTTPBasicAuth

def test_instagram_scan():
    # Retrieve username and password from environment variables
    username = os.getenv('API_USERNAME')
    password = os.getenv('API_PASSWORD')
    
    # API endpoint
    url = "http://localhost:8000/instagram/scan"  # For local testing

    # Make a GET request with basic authentication
    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password)
    )

    posts = response.json()
    
    print(f"\nFound {len(posts)} matching posts:")
    for post in posts:
        print(f"\nComment: {post['content'][:200]}...")  # Show first 200 chars of content
        print(f"By: {post['author']}")
        print(f"URL: {post['url']}")
        print(f"Likes: {post['likes']}")
        print(f"Matched keyword: {post['keyword_matched']}")

if __name__ == "__main__":
    test_instagram_scan() 