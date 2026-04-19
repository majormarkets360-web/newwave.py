from __future__ import annotations
import os, io, base64, json, time
import requests
from typing import Optional

# ── Anthropic ─────────────────────────────────────────────────────────────────
def generate_caption_and_hashtags(
    topic: str,
    platform: str,
    tone: str,
    brand_voice: str = "",
    api_key: str = "",
) -> dict:
    """
    Uses Claude to produce platform-optimised caption + hashtags + CTA.
    Returns {"caption": str, "hashtags": list[str], "cta": str, "script": str}
    """
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return _fallback_caption(topic, platform, tone)

    from anthropic import Anthropic
    client = Anthropic(api_key=key)

    platform_limits = {
        "Instagram": 2200, "TikTok": 2200, "X / Twitter": 230,
        "LinkedIn": 3000, "Facebook": 1000, "YouTube Shorts": 500,
    }
    char_limit = platform_limits.get(platform, 2000)
    hashtag_limit = 3 if platform == "X / Twitter" else (5 if platform == "LinkedIn" else 20)

    system = (
        "You are an elite social media content strategist and copywriter. "
        "You write viral, high-converting social media content. "
        "Always respond with a valid JSON object only — no markdown fences."
    )
    user_msg = f"""Generate social media content for the following brief:

Topic: {topic}
Platform: {platform}
Tone: {tone}
Brand voice: {brand_voice or 'Professional yet approachable'}
Character limit: {char_limit}
Max hashtags: {hashtag_limit}

Return a JSON object with these exact keys:
- "caption": engaging {platform} caption (max {char_limit} chars, NO hashtags inline)
- "hashtags": array of {hashtag_limit} trending, relevant hashtags (without # symbol)
- "cta": punchy call-to-action phrase (max 10 words)
- "script": 30-second verbal script/voiceover for a video version
- "hook": the first sentence to stop the scroll (max 15 words)
- "best_post_time": recommended posting window for maximum reach
"""

    try:
        resp = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        raw = resp.content[0].text.strip()
        # strip markdown fences if model adds them
        raw = raw.replace("```json", "").replace("```", "").strip()
        return json.loads(raw)
    except Exception as e:
        return {**_fallback_caption(topic, platform, tone), "error": str(e)}


def generate_content_strategy(topic: str, platforms: list[str], api_key: str = "") -> str:
    """Returns a multi-platform content strategy as markdown."""
    key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        return "⚠️ Add your Anthropic API key to generate a strategy."

    from anthropic import Anthropic
    client = Anthropic(api_key=key)

    resp = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1500,
        messages=[
            {
                "role": "user",
                "content": (
                    f"Create a detailed, actionable social media content strategy for: '{topic}'. "
                    f"Platforms: {', '.join(platforms)}. "
                    "Include: posting frequency, content pillars, engagement tactics, "
                    "growth strategies, and a 7-day content calendar. "
                    "Format as clean markdown."
                ),
            }
        ],
    )
    return resp.content[0].text


def _fallback_caption(topic: str, platform: str, tone: str) -> dict:
    return {
        "caption": (
            f"✨ {topic} — crafted with intention and purpose. "
            "What do you think? Drop your thoughts below! 👇"
        ),
        "hashtags": [
            topic.replace(" ", ""),
            "ContentCreator",
            "SocialMedia",
            "Trending",
            "Viral",
            "NewPost",
            "MustSee",
            "Explore",
        ],
        "cta": "Follow for daily inspiration!",
        "script": f"Hey everyone! Today we're talking about {topic}. Stay tuned!",
        "hook": f"You won't believe what {topic} can do for you...",
        "best_post_time": "6-9 PM on weekdays",
    }


# ── Stability AI Image Generation ────────────────────────────────────────────
def generate_image_stability(
    prompt: str,
    negative_prompt: str = "blurry, watermark, text, logo, ugly, low quality",
    width: int = 1024,
    height: int = 1024,
    steps: int = 30,
    cfg_scale: float = 7.0,
    api_key: str = "",
) -> Optional[bytes]:
    """
    Calls Stability AI SDXL via REST. Returns PNG bytes or None on failure.
    """
    key = api_key or os.getenv("STABILITY_API_KEY", "")
    if not key:
        return None

    url = "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image"
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    body = {
        "text_prompts": [
            {"text": prompt, "weight": 1.0},
            {"text": negative_prompt, "weight": -1.0},
        ],
        "cfg_scale": cfg_scale,
        "height": height,
        "width": width,
        "steps": steps,
        "samples": 1,
    }

    try:
        resp = requests.post(url, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        img_b64 = data["artifacts"][0]["base64"]
        return base64.b64decode(img_b64)
    except Exception as e:
        print(f"Stability AI error: {e}")
        return None


# ── Replicate Video Generation ────────────────────────────────────────────────
def generate_video_replicate(
    prompt: str,
    model: str = "minimax/video-01",
    api_key: str = "",
) -> Optional[str]:
    """
    Submits a video generation job to Replicate. Returns output URL or None.
    Model options:
      - minimax/video-01 (free tier)
      - luma-ai/dream-machine
      - stability-ai/stable-video-diffusion
    """
    key = api_key or os.getenv("REPLICATE_API_KEY", "")
    if not key:
        return None

    try:
        import replicate
        client = replicate.Client(api_token=key)
        output = client.run(model, input={"prompt": prompt})
        if isinstance(output, list):
            return output[0]
        return str(output)
    except Exception as e:
        print(f"Replicate error: {e}")
        return None


# ── Image from URL helper ─────────────────────────────────────────────────────
def fetch_image_bytes(url: str) -> Optional[bytes]:
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        return resp.content
    except Exception:
        return None

