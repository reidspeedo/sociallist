import requests

def test_reddit_scan():
    response = requests.get('http://localhost:8000/reddit/scan')
    posts = response.json()
    
    print(f"\nFound {len(posts)} matching posts:")
    for post in posts:
        print(f"\n{post['title']}")
        print(f"r/{post['subreddit']} - {post['url']}")

if __name__ == "__main__":
    test_reddit_scan() 