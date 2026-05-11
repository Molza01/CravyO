from apify_client import ApifyClient
import os, json
from dotenv import load_dotenv

load_dotenv()
client = ApifyClient(os.environ["APIFY_API_TOKEN"])

def scrape_instagram(username: str, max_posts: int = 15) -> list:
    """Scrapes Instagram profile and returns posts."""
    try:
        url = f"https://www.instagram.com/{username}/"
        print(f"[SCRAPER] Starting Instagram scrape for: {url}")
        
        run = client.actor("apify/instagram-scraper").call(run_input={
            "directUrls": [url],
            "resultsType": "posts",
            "resultsLimit": max_posts,
        })
        
        dataset_id = run["defaultDatasetId"]
        print(f"[SCRAPER] Dataset ID: {dataset_id}")
        
        items = list(client.dataset(dataset_id).iterate_items())
        print(f"[SCRAPER] Raw items returned: {len(items)}")
        
        if not items:
            print("[SCRAPER] WARNING: Apify returned ZERO items. Possible reasons:")
            print("  - Instagram blocked the request (very common)")
            print("  - Profile is private")
            print("  - Username does not exist")
            print("  - Apify actor needs Instagram login cookies")
            return []
        
        # Show first raw item for debugging
        print(f"[SCRAPER] First raw item keys: {list(items[0].keys())}")
        
        posts = [{
            "caption": i.get("caption", ""),
            "hashtags": i.get("hashtags", []),
            "timestamp": i.get("timestamp", ""),
            "thumbnail_url": i.get("displayUrl", ""),
            "likes": i.get("likesCount", 0),
        } for i in items]
        
        print(f"[SCRAPER] Parsed {len(posts)} posts successfully")
        return posts
        
    except Exception as e:
        print(f"[SCRAPER ERROR] Instagram scrape failed: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    username = input("Enter Instagram username: ").strip()
    posts = scrape_instagram(username, max_posts=5)
    print("\n" + "="*50)
    print(f"Total posts: {len(posts)}")
    for i, p in enumerate(posts[:2]):
        print(f"\nPost {i+1}: {p['caption'][:100]}...")
    print("="*50)