"""
YouTube Service — Apify-based scraper (stub with mock fallback).
"""

from apify_client import ApifyClient
import os
from dotenv import load_dotenv

load_dotenv()

def scrape_youtube(channel_handle: str, max_videos: int = 10) -> list:
    """Scrape YouTube channel for recent video titles/descriptions."""
    try:
        client = ApifyClient(os.environ["APIFY_API_TOKEN"])
        url = f"https://www.youtube.com/@{channel_handle}"
        print(f"[SCRAPER] Scraping YouTube: {url}")

        run = client.actor("bernardo/youtube-scraper").call(run_input={
            "startUrls": [{"url": url}],
            "maxResults": max_videos,
        })

        items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        print(f"[SCRAPER] YouTube returned {len(items)} items")

        return [{
            "title": i.get("title", ""),
            "caption": i.get("description", ""),
            "hashtags": i.get("hashtags", []),
            "thumbnail_url": i.get("thumbnailUrl", ""),
        } for i in items]

    except Exception as e:
        print(f"[SCRAPER ERROR] YouTube failed: {e}")
        return []
