from __future__ import annotations
import random

# ── Preset Categories ─────────────────────────────────────────────────────────
PRESET_CATEGORIES: dict[str, list[str]] = {
    "🚀 Business & Entrepreneurship": [
        "5 morning habits of successful CEOs",
        "How to bootstrap a startup to $1M",
        "LinkedIn growth strategy for 2025",
        "Passive income ideas that actually work",
        "How to network like a pro",
    ],
    "💡 Technology & AI": [
        "Best AI tools for productivity in 2025",
        "How ChatGPT is changing content creation",
        "10 Chrome extensions that save hours",
        "The future of remote work with AI",
        "Prompt engineering tips for beginners",
    ],
    "💪 Health & Wellness": [
        "Morning yoga routine for beginners",
        "5-minute meditation for busy people",
        "High protein meal prep under $50",
        "How to fix your sleep schedule fast",
        "Daily habits for mental clarity",
    ],
    "🎨 Content Creation": [
        "How to go viral on TikTok in 2025",
        "Instagram Reels strategy that works",
        "YouTube Shorts vs long-form content",
        "Building a personal brand from zero",
        "Best camera gear for beginners",
    ],
    "💰 Finance & Investing": [
        "Index funds explained in 60 seconds",
        "How to budget with the 50/30/20 rule",
        "Crypto investing for beginners 2025",
        "Real estate vs stocks — what wins?",
        "Side hustles earning $500/month",
    ],
    "🌍 Travel & Lifestyle": [
        "10 underrated travel destinations 2025",
        "How to travel Europe on $50/day",
        "Digital nomad starter guide",
        "Best travel credit card rewards",
        "Solo travel safety tips",
    ],
    "🍕 Food & Recipes": [
        "5-ingredient meals under 20 minutes",
        "Trending TikTok recipes to try now",
        "Healthy desserts that taste indulgent",
        "Meal prep Sunday — full week plan",
        "Budget gourmet cooking hacks",
    ],
    "📚 Education & Self-Development": [
        "Books that changed my life this year",
        "How to learn any skill in 20 hours",
        "The Feynman technique explained",
        "Building a second brain with Notion",
        "Daily reading habit — how to start",
    ],
}

# ── Platform Formats ──────────────────────────────────────────────────────────
PLATFORM_FORMATS: dict[str, dict] = {
    "Instagram": {
        "video_ratio": "9:16 or 1:1",
        "image_ratio": "1:1 (square)",
        "max_caption": 2200,
        "hashtag_limit": 30,
        "best_times": ["6:00 AM", "12:00 PM", "7:00 PM"],
        "max_duration": 90,
    },
    "TikTok": {
        "video_ratio": "9:16",
        "image_ratio": "9:16",
        "max_caption": 2200,
        "hashtag_limit": 5,
        "best_times": ["7:00 AM", "3:00 PM", "8:00 PM"],
        "max_duration": 600,
    },
    "X / Twitter": {
        "video_ratio": "16:9",
        "image_ratio": "16:9",
        "max_caption": 280,
        "hashtag_limit": 3,
        "best_times": ["8:00 AM", "12:00 PM", "5:00 PM"],
        "max_duration": 140,
    },
    "LinkedIn": {
        "video_ratio": "16:9 or 1:1",
        "image_ratio": "1.91:1",
        "max_caption": 3000,
        "hashtag_limit": 5,
        "best_times": ["7:00 AM", "10:00 AM", "12:00 PM"],
        "max_duration": 600,
    },
    "Facebook": {
        "video_ratio": "16:9",
        "image_ratio": "1.91:1",
        "max_caption": 63206,
        "hashtag_limit": 10,
        "best_times": ["9:00 AM", "1:00 PM", "3:00 PM"],
        "max_duration": 240,
    },
    "YouTube Shorts": {
        "video_ratio": "9:16",
        "image_ratio": "9:16",
        "max_caption": 5000,
        "hashtag_limit": 15,
        "best_times": ["12:00 PM", "3:00 PM", "7:00 PM"],
        "max_duration": 60,
    },
}

# ── Trending Pool ─────────────────────────────────────────────────────────────
_TRENDING_POOL: list[dict] = [
    {"category": "🤖 AI & Tech",     "title": "How AI agents are replacing entire job roles in 2025"},
    {"category": "🤖 AI & Tech",     "title": "GPT-5 vs Claude — which AI wins for content creation?"},
    {"category": "🤖 AI & Tech",     "title": "The AI tools every entrepreneur needs right now"},
    {"category": "🤖 AI & Tech",     "title": "Building AI-powered apps without coding"},
    {"category": "💼 Business",      "title": "Why most startups fail in year two (and how to survive)"},
    {"category": "💼 Business",      "title": "The one-person business model taking over LinkedIn"},
    {"category": "💼 Business",      "title": "How to turn your expertise into a $10K/month offer"},
    {"category": "💼 Business",      "title": "Cold outreach templates that get 30% reply rates"},
    {"category": "📱 Social Media",  "title": "The Instagram algorithm changed — here's what works now"},
    {"category": "📱 Social Media",  "title": "Why faceless YouTube channels are exploding in 2025"},
    {"category": "📱 Social Media",  "title": "TikTok SEO — how to rank your videos on search"},
    {"category": "📱 Social Media",  "title": "LinkedIn carousel posts that went viral this week"},
    {"category": "💰 Finance",       "title": "Stock market outlook — what analysts are saying now"},
    {"category": "💰 Finance",       "title": "The passive income stack earning $5K/month"},
    {"category": "💰 Finance",       "title": "ETFs vs individual stocks — what wins long term"},
    {"category": "🌱 Wellness",      "title": "The 5 AM routine that changed my productivity forever"},
    {"category": "🌱 Wellness",      "title": "Why cold plunging is dominating wellness content"},
    {"category": "🌱 Wellness",      "title": "Evidence-based supplements actually worth taking"},
    {"category": "🎬 Entertainment", "title": "Most anticipated movies releasing this month"},
    {"category": "🎬 Entertainment", "title": "The podcasts every ambitious person is listening to"},
    {"category": "🌍 Travel",        "title": "The cheapest flights in 2025 — where to book now"},
    {"category": "🌍 Travel",        "title": "Remote work visas — countries welcoming digital nomads"},
    {"category": "🍕 Food",          "title": "The TikTok recipe everyone is making this week"},
    {"category": "🍕 Food",          "title": "High-protein meals for under $5 — meal prep edition"},
]


def get_trending_topics(n: int = 12, category: str | None = None) -> list[dict]:
    """Returns n trending topic dicts with 'category' and 'title' keys."""
    pool = (
        [t for t in _TRENDING_POOL if t["category"] == category]
        if category
        else _TRENDING_POOL
    )
    shuffled = pool.copy()
    random.shuffle(shuffled)
    return shuffled[:n]
