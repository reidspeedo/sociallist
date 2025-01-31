import requests
import os
from requests.auth import HTTPBasicAuth

def test_twitter_communities():
    # Retrieve username and password from environment variables
    username = os.getenv('API_USERNAME')
    password = os.getenv('API_PASSWORD')
    
    # API endpoint
    url = "http://localhost:8000/twitter/communities"  # For local testing

    # Make a GET request with basic authentication
    response = requests.get(
        url,
        auth=HTTPBasicAuth(username, password)
    )

    posts = response.json()
    
    print(f"\nFound {len(posts)} matching posts:")
    for post in posts:
        print(f"\n{post['content'][:200]}...")  # Show first 200 chars of content
        print(f"Community: {post['community']}")
        print(f"By @{post['author']} - {post['url']}")
        print(f"Likes: {post['likes']}, Retweets: {post['retweets']}")

if __name__ == "__main__":
    test_twitter_communities() 