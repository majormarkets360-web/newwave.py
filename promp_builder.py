prompt_builder.py
Builds richly-detailed visual and caption prompts tuned for each social platform.
"""
from __future__ import annotations

STYLE_PRESETS: dict[str, str] = {
    "Cinematic": (
        "cinematic wide-angle shot, dramatic lighting, film grain, "
        "anamorphic lens flare, shallow depth of field, color graded, "
        "professional photography, 8K resolution"
    ),
    "Minimal & Clean": (
        "minimalist composition, clean white background, soft diffused light, "
        "negative space, editorial style, product photography aesthetic"
    ),
    "Vibrant & Bold": (
        "vivid saturated colors, high contrast, energetic composition, "
        "dynamic angles, bold typography space, lifestyle photography"
    ),
    "Dark & Moody": (
        "dark moody atmosphere, deep shadows, low-key lighting, "
        "chiaroscuro, dramatic, editorial fashion photography"
    ),
    "Natural & Authentic": (
        "natural golden hour lighting, candid lifestyle photography, "
        "warm tones, authentic moment, environmental portrait"
    ),
    "Futuristic / Tech": (
        "neon cyberpunk aesthetic, holographic UI elements, "
        "dark background with glowing accents, sci-fi atmosphere, "
        "highly detailed 3D render"
    ),
    "Luxury & Premium": (
        "luxury brand aesthetic, marble textures, gold accents, "
        "high-end product photography, soft bokeh, aspirational lifestyle"
    ),
}

TONE_PRESETS: dict[str, str] = {
    "Inspirational": "uplifting, motivating, empowering, positive energy",
    "Educational": "informative, clear, authoritative, trustworthy",
    "Entertaining": "fun, engaging, surprising, shareable",
    "Promotional": "compelling, benefit-focused, call-to-action driven",
    "Storytelling": "narrative arc, emotional connection, authentic voice",
    "Trendy": "current, relatable, culturally relevant, viral potential",
}

PLATFORM_IMAGE_SPECS: dict[str, str] = {
    "Instagram": "square 1:1 composition, bright engaging colors, mobile-first design",
    "TikTok": "vertical 9:16 format, bold hook in first frame, text-overlay friendly",
    "X / Twitter": "16:9 widescreen composition, news-worthy framing, high contrast",
    "LinkedIn": "professional setting, 1.91:1 ratio, business context, clean layout",
    "Facebook": "eye-catching thumbnail, 1.91:1, broad audience appeal",
    "YouTube Shorts": "vertical 9:16, high-energy thumbnail, bold title space at top",
}


def build_image_prompt(
    topic: str,
    platform: str,
    style: str,
    tone: str,
    extra_context: str = "",
) -> str:
    style_desc = STYLE_PRESETS.get(style, style)
    tone_desc = TONE_PRESETS.get(tone, tone)
    platform_spec = PLATFORM_IMAGE_SPECS.get(platform, "")

    prompt = (
        f"{topic}, {style_desc}, {tone_desc} mood, "
        f"optimized for {platform} — {platform_spec}, "
        "ultra-high quality, professional social media content, "
        "no watermarks, no text overlays"
    )
    if extra_context:
        prompt += f", {extra_context}"
    return prompt


def build_video_prompt(
    topic: str,
    platform: str,
    style: str,
    tone: str,
    duration: str = "15 seconds",
    extra_context: str = "",
) -> str:
    style_desc = STYLE_PRESETS.get(style, style)
    tone_desc = TONE_PRESETS.get(tone, tone)

    prompt = (
        f"A {duration} social media video about: {topic}. "
        f"Visual style: {style_desc}. "
        f"Emotional tone: {tone_desc}. "
        f"Platform: {platform}. "
        "High production value, smooth transitions, "
        "engaging throughout, professional grade."
    )
    if extra_context:
        prompt += f" Additional context: {extra_context}"
    return prompt


def build_quickframe_brief(
    topic: str,
    platform: str,
    style: str,
    tone: str,
    brand_name: str = "",
    brand_colors: str = "",
    cta: str = "",
) -> dict:
    """
    Returns a structured brief that maps to QuickFrame AI's UI fields
    so the user can paste / fill them in quickly.
    """
    return {
        "script_prompt": (
            f"Create a {tone.lower()} {platform} video ad about: {topic}. "
            f"Visual style: {style}. "
            + (f"Brand: {brand_name}. " if brand_name else "")
            + (f"Brand colors: {brand_colors}. " if brand_colors else "")
            + (f"End with CTA: {cta}." if cta else "")
        ),
        "style": style,
        "platform": platform,
        "tone": tone,
        "topic": topic,
        "brand_name": brand_name,
        "cta": cta or f"Follow for more {topic} content!",
    }

