
from __future__ import annotations
import requests
import json
from datetime import datetime

# ── Static curated presets ────────────────────────────────────────────────────
PRESET_CATEGORIES: dict[str, list[str]] = {
    "🔥 Lifestyle": [
        "Morning routine that changed my life",
        "Minimalist home aesthetic",
        "Healthy meal prep Sunday",
        "Self-care day reset",
        "Digital detox challenge",
    ],
    "💼 Business": [
        "Side hustle success story",
        "Productivity hacks for entrepreneurs",
        "Work-from-home setup tour",
        "Passive income streams 2025",
        "Personal brand building tips",
    ],
    "🤖 Tech & AI": [
        "AI tools changing everything in 2025",
        "Future of automation",
        "Prompt engineering secrets",
        "Best AI apps for creators",
        "Tech gadget unboxing",
    ],
    "🎨 Creative": [
        "Behind the scenes of my creative process",
        "Aesthetic transformation video",
        "Art challenge viral moment",
        "Photography tips for beginners",
        "Color grading cinematic look",
    ],
    "🌍 Culture & Trends": [
        "This week's biggest cultural moment",
        "Viral food trend review",
        "Travel destination underrated gem",
        "Fashion trend breakdown",
        "Pop culture opinion hot take",
    ],
    "💪 Fitness & Wellness": [
        "30-day fitness transformation",
        "Mental health awareness story",
        "Gym motivation reel",
        "Clean eating week challenge",
        "Yoga for beginners flow",
    ],
}

PLATFORM_FORMATS: dict[str, dict] = {
    "Instagram": {
        "image_ratio": "1:1",
        "video_ratio": "9:16",
        "max_caption": 2200,
        "hashtag_limit": 30,
        "best_times": ["6-9 AM", "12-2 PM", "7-9 PM"],
        "formats": ["Single Image", "Carousel", "Reel", "Story"],
    },
    "TikTok": {
        "image_ratio": "9:16",
        "video_ratio": "9:16",
        "max_caption": 2200,
        "hashtag_limit": 10,
        "best_times": ["7-9 AM", "12-3 PM", "7-11 PM"],
        "formats": ["Short Video 15s", "Long Video 60s", "Photo Slideshow"],
    },
    "X / Twitter": {
        "image_ratio": "16:9",
        "video_ratio": "16:9",
        "max_caption": 280,
        "hashtag_limit": 3,
        "best_times": ["8-10 AM", "12-1 PM", "5-6 PM"],
        "formats": ["Tweet + Image", "Thread", "Video Tweet"],
    },
    "LinkedIn": {
        "image_ratio": "1.91:1",
        "video_ratio": "16:9",
        "max_caption": 3000,
        "hashtag_limit": 5,
        "best_times": ["8-10 AM", "12 PM", "5-6 PM"],
        "formats": ["Article Post", "Image Post", "Video Post", "Document Carousel"],
    },
    "Facebook": {
        "image_ratio": "1.91:1",
        "video_ratio": "16:9",
        "max_caption": 63206,
        "hashtag_limit": 10,
        "best_times": ["1-3 PM", "7-9 PM"],
        "formats": ["Post + Image", "Story", "Reel", "Event"],
    },
    "YouTube Shorts": {
        "image_ratio": "9:16",
        "video_ratio": "9:16",
        "max_caption": 5000,
        "hashtag_limit": 15,
        "best_times": ["2-4 PM", "8-10 PM"],
        "formats": ["Short (< 60s)", "Community Post"],
    },
}


def get_trending_topics(limit: int = 8) -> list[dict]:
    """
    Attempt to fetch live trending topics via DuckDuckGo Trending.
    Falls back to a curated list when the network call fails.
    Returns list of {title, source, category} dicts.
    """
    topics: list[dict] = []

    # ── Attempt 1: DuckDuckGo Trending (no API key needed) ────────────────────
    try:
        resp = requests.get(
            "https://duckduckgo.com/news.js",
            params={"q": "trending", "o": "json", "l": "us-en", "s": "0", "vqd": ""},
            timeout=4,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        if resp.ok:
            data = resp.json()
            for item in data.get("results", [])[:limit]:
                topics.append(
                    {
                        "title": item.get("title", ""),
                        "source": item.get("source", "DuckDuckGo"),
                        "category": "🌐 Live Trend",
                        "url": item.get("url", ""),
                    }
                )
    except Exception:
        pass

    # ── Attempt 2: GitHub trending topics API ─────────────────────────────────
    if len(topics) < limit:
        try:
            resp = requests.get(
                "https://api.github.com/search/repositories",
                params={
                    "q": "created:>2025-01-01",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 5,
                },
                timeout=4,
            )
            if resp.ok:
                for repo in resp.json().get("items", []):
                    topics.append(
                        {
                            "title": f"Tech Trend: {repo['name']} — {repo.get('description','')[:60]}",
                            "source": "GitHub",
                            "category": "🤖 Tech & AI",
                            "url": repo.get("html_url", ""),
                        }
                    )
        except Exception:
            pass

    # ── Fallback: inject curated presets ─────────────────────────────────────
    if len(topics) < 4:
        import random
        for cat, items in PRESET_CATEGORIES.items():
            for item in random.sample(items, min(2, len(items))):
                topics.append(
                    {"title": item, "source": "Curated", "category": cat, "url": ""}
                )
                if len(topics) >= limit:
                    break
            if len(topics) >= limit:
                break

    return topics[:limit]

