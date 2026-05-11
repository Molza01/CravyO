"""
YouTube Service — Scrape YouTube channel videos for food detection.
Uses Apify YouTube scraper actor with proper error handling.
"""

import os
from dotenv import load_dotenv

load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_API_TOKEN")


def scrape_youtube(channel_handle: str, max_videos: int = 10) -> list:
    """
    Scrape YouTube channel for recent video titles/descriptions.
    Tries multiple approaches in order of preference.
    """
    # Clean the handle
    handle = channel_handle.strip()
    if handle.startswith("@"):
        url = f"https://www.youtube.com/{handle}"
    elif "/" in handle:
        url = handle if handle.startswith("http") else f"https://www.youtube.com/{handle}"
    else:
        url = f"https://www.youtube.com/@{handle}"

    print(f"[SCRAPER] Scraping YouTube: {url}")

    # Try Apify YouTube Scraper actor
    posts = _scrape_with_apify(url, max_videos)
    if posts:
        return posts

    # Fallback: Try web scraping directly
    posts = _scrape_web(url, max_videos)
    if posts:
        return posts

    print("[SCRAPER] All YouTube scraping methods failed")
    return []


def _scrape_with_apify(url: str, max_videos: int) -> list:
    """Scrape using Apify YouTube scraper."""
    try:
        from apify_client import ApifyClient
    except ImportError:
        print("[SCRAPER] Apify client not installed")
        return []

    if not APIFY_TOKEN:
        print("[SCRAPER] No Apify API token found")
        return []

    try:
        client = ApifyClient(APIFY_TOKEN)

        # Try the proper YouTube scraper actor
        run = client.actor("apify/youtube-scraper").call(run_input={
            "startUrls": [{"url": url}],
            "maxResults": max_videos,
        })

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"[SCRAPER] YouTube returned {len(items)} items")

        if not items:
            return []

        return [{
            "title": i.get("title", ""),
            "caption": i.get("description", ""),
            "hashtags": i.get("hashtags", []),
            "tags": i.get("tags", []),
            "thumbnail_url": i.get("thumbnailUrl", ""),
        } for i in items]

    except Exception as e:
        print(f"[SCRAPER ERROR] Apify YouTube scrape failed: {e}")
        return []


def _scrape_web(url: str, max_videos: int) -> list:
    """Fallback: Direct web scraping using requests + BeautifulSoup."""
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("[SCRAPER] requests or bs4 not installed for fallback scraping")
        return []

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        }

        # Extract channel ID from URL
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code != 200:
            print(f"[SCRAPER] YouTube returned status {response.status_code}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')

        # Try to find video links on the page
        videos = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/watch?v=' in href:
                video_id = href.split('v=')[1].split('&')[0]
                title = link.get_text(strip=True)
                if title and video_id not in [v.get('video_id') for v in videos]:
                    videos.append({
                        "title": title,
                        "caption": "",
                        "hashtags": [],
                        "tags": [],
                        "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                        "video_id": video_id,
                        "url": f"https://www.youtube.com/watch?v={video_id}",
                    })
                    if len(videos) >= max_videos:
                        break

        # If we found videos, try to get descriptions
        for video in videos[:5]:
            try:
                video_response = requests.get(video["url"], headers=headers, timeout=10)
                video_soup = BeautifulSoup(video_response.text, 'html.parser')
                desc_tag = video_soup.find('meta', {'name': 'description'})
                if desc_tag:
                    video["caption"] = desc_tag.get('content', '')
                tags_content = video_soup.find_all('meta', {'property': 'og:video:tag'})
                if tags_content:
                    video["tags"] = [tag.get('content', '') for tag in tags_content if tag.get('content')]
            except Exception:
                pass

        print(f"[SCRAPER] Web scrape found {len(videos)} videos")
        return videos

    except Exception as e:
        print(f"[SCRAPER ERROR] Web scraping failed: {e}")
        return []


if __name__ == "__main__":
    handle = input("Enter YouTube channel handle (e.g., 'foodie' or '@foodie'): ").strip()
    posts = scrape_youtube(handle, max_videos=5)
    print("\n" + "=" * 50)
    print(f"Total posts: {len(posts)}")
    for i, p in enumerate(posts[:3]):
        print(f"\nVideo {i+1}: {p.get('title', 'No title')[:80]}")
        print(f"   Description: {p.get('caption', 'No caption')[:150]}...")
    print("=" * 50)