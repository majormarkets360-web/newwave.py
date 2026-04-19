from __future__ import annotations
import os, io, json, time, base64, textwrap
from datetime import datetime
from typing import Optional

import streamlit as st
from PIL import Image
    
# ── Local utils ───────────────────────────────────────────────────────────────
from utils.trending import get_trending_topics, PRESET_CATEGORIES, PLATFORM_FORMATS
from utils.prompt_builder import (
    build_image_prompt,
    build_video_prompt,
    build_quickframe_brief,
    STYLE_PRESETS,
    TONE_PRESETS,
)
from utils.ai_generator import (
    generate_caption_and_hashtags,
    generate_content_strategy,
    generate_image_stability,
    generate_video_replicate,
    fetch_image_bytes,
)
from utils.social_poster import (
    post_to_twitter,
    post_to_linkedin,
    post_to_facebook,
    post_to_instagram,
    summarise_results,
)
@st.cache_data(show_spinner=False)
def _get_platform_names():
    return list(PLATFORM_FORMATS.keys())

@st.cache_data(show_spinner=False)  
def _get_style_names():
    return list(STYLE_PRESETS.keys())

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Social Studio",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://ai.quickframe.com",
        "Report a bug": None,
        "About": "AI Social Media Content Studio powered by QuickFrame AI & Claude",
    },
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* ── Global ──────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Header banner ───────────────────────────────── */
.studio-header {
    background: linear-gradient(135deg, #1e0a3c 0%, #0f172a 50%, #0a1628 100%);
    border: 1px solid #7c3aed44;
    border-radius: 16px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.studio-header::before {
    content: '';
    position: absolute; inset: 0;
    background: radial-gradient(ellipse at 20% 50%, #7c3aed22 0%, transparent 60%),
                radial-gradient(ellipse at 80% 20%, #2563eb22 0%, transparent 60%);
}
.studio-header h1 {
    font-size: 2rem; font-weight: 700; margin: 0;
    background: linear-gradient(135deg, #a78bfa, #60a5fa, #f472b6);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.studio-header p { color: #94a3b8; margin: 0.4rem 0 0; font-size: 1rem; }

/* ── Cards ───────────────────────────────────────── */
.content-card {
    background: #1a1a2e;
    border: 1px solid #2d2d4a;
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    transition: border-color 0.2s;
}
.content-card:hover { border-color: #7c3aed66; }

/* ── Trend chips ─────────────────────────────────── */
.trend-chip {
    display: inline-block;
    background: linear-gradient(135deg, #1e0a3c, #0f172a);
    border: 1px solid #7c3aed55;
    border-radius: 20px;
    padding: 0.3rem 0.85rem;
    font-size: 0.8rem;
    color: #c4b5fd;
    margin: 0.2rem;
    cursor: pointer;
    transition: all 0.2s;
}
.trend-chip:hover { background: #7c3aed33; border-color: #7c3aed; }

/* ── Platform badges ─────────────────────────────── */
.platform-badge {
    display: inline-flex; align-items: center; gap: 0.4rem;
    background: #0f172a; border: 1px solid #2d2d4a;
    border-radius: 8px; padding: 0.4rem 0.8rem;
    font-size: 0.85rem; color: #e2e8f0; margin: 0.15rem;
}

/* ── Success banner ──────────────────────────────── */
.success-banner {
    background: linear-gradient(135deg, #064e3b, #065f46);
    border: 1px solid #10b981;
    border-radius: 10px; padding: 1rem 1.5rem;
}

/* ── Metrics ─────────────────────────────────────── */
.metric-box {
    background: #1a1a2e; border: 1px solid #2d2d4a;
    border-radius: 10px; padding: 1rem; text-align: center;
}
.metric-box .value { font-size: 1.8rem; font-weight: 700; color: #a78bfa; }
.metric-box .label { font-size: 0.8rem; color: #64748b; margin-top: 0.2rem; }

/* ── QuickFrame embed ────────────────────────────── */
.qf-container {
    border: 1px solid #7c3aed66;
    border-radius: 12px; overflow: hidden;
}

/* ── Sidebar ─────────────────────────────────────── */
section[data-testid="stSidebar"] { background: #0d0d1a; border-right: 1px solid #1e1e3a; }
</style>
""",
    unsafe_allow_html=True,
)

# ── Session state defaults ─────────────────────────────────────────────────────
def _init_state():
    defaults = {
        "topic": "",
        "generated_caption": None,
        "generated_hashtags": [],
        "generated_cta": "",
        "generated_script": "",
        "generated_hook": "",
        "image_bytes": None,
        "video_url": None,
        "post_results": {},
        "strategy_md": "",
        "api_keys_saved": False,
        "post_history": [],
        "scheduled_posts": [],
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# ═══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("### 🔑 API Configuration")
    with st.expander("Add API Keys", expanded=not st.session_state.api_keys_saved):
        anthropic_key = st.text_input(
            "Anthropic (Claude)", type="password",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            help="Get at console.anthropic.com",
        )
        stability_key = st.text_input(
            "Stability AI", type="password",
            value=os.getenv("STABILITY_API_KEY", ""),
            help="Get at platform.stability.ai",
        )
        replicate_key = st.text_input(
            "Replicate (Video)", type="password",
            value=os.getenv("REPLICATE_API_KEY", ""),
            help="Get at replicate.com/account",
        )

        st.markdown("---")
        st.markdown("**Social Platforms**")
        tw_col1, tw_col2 = st.columns(2)
        twitter_api_key = tw_col1.text_input("X API Key", type="password")
        twitter_api_secret = tw_col2.text_input("X API Secret", type="password")
        twitter_access_token = tw_col1.text_input("X Access Token", type="password")
        twitter_access_secret = tw_col2.text_input("X Access Secret", type="password")

        linkedin_token = st.text_input("LinkedIn Access Token", type="password")
        linkedin_urn = st.text_input("LinkedIn Person URN", placeholder="urn:li:person:XXXX")

        fb_token = st.text_input("Facebook Page Token", type="password")
        fb_page_id = st.text_input("Facebook Page ID")

        ig_token = st.text_input("Instagram Access Token", type="password")
        ig_user_id = st.text_input("Instagram User ID")

        if st.button("💾 Save Keys", use_container_width=True):
            st.session_state.api_keys_saved = True
            st.success("Keys saved for this session!")

    st.markdown("---")

    st.markdown("### 📊 Session Stats")
    col_a, col_b = st.columns(2)
    col_a.metric("Posts Created", len(st.session_state.post_history))
    col_b.metric("Platforms", len(PLATFORM_FORMATS))

    st.markdown("---")
    st.markdown("### 🎨 Quick Style")
    quick_style = st.selectbox(
        "Default Visual Style",
        list(STYLE_PRESETS.keys()),
        index=0,
    )
    quick_tone = st.selectbox(
        "Default Tone",
        list(TONE_PRESETS.keys()),
        index=0,
    )

    st.markdown("---")
    st.markdown(
        "<small style='color:#475569'>Powered by QuickFrame AI · Claude · Stability AI</small>",
        unsafe_allow_html=True,
    )

# ═══════════════════════════════════════════════════════════════════════════════
# HEADER
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown(
    """
<div class="studio-header">
  <h1>🎬 AI Social Media Content Studio</h1>
  <p>Autonomously generate, refine, and publish picture-perfect content across every platform</p>
</div>
""",
    unsafe_allow_html=True,
)

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN TABS
# ═══════════════════════════════════════════════════════════════════════════════
tab_create, tab_studio, tab_publish, tab_schedule, tab_strategy, tab_history = st.tabs(
    ["✨ Create", "🎨 QuickFrame Studio", "🚀 Publish", "📅 Schedule", "📈 Strategy", "📚 History"]
)

# ══════════════════════════════════════════════════
# TAB 1 — CREATE
# ══════════════════════════════════════════════════
with tab_create:
    left, right = st.columns([1.1, 0.9], gap="large")

    # ── Left panel — topic & settings ─────────────────────────────────────
    with left:
        st.markdown("#### 🎯 What's your content about?")

        # ── Topic input ────────────────────────────────────────────────────
        topic_input = st.text_input(
            "Topic / Subject",
            placeholder='e.g. "Morning yoga routine for beginners" or "AI productivity tips 2025"',
            value=st.session_state.topic,
            label_visibility="collapsed",
        )
        if topic_input:
            st.session_state.topic = topic_input

        # ── Trending topics ────────────────────────────────────────────────
        with st.expander("🔥 Trending Topics & Presets", expanded=True):
            tab_live, tab_presets = st.tabs(["Live Trends", "Preset Categories"])

            with tab_live:
                if st.button("🔄 Refresh Trends", use_container_width=True):
                    with st.spinner("Fetching live trends..."):
                        st.session_state["live_trends"] = get_trending_topics(12)

                if "live_trends" not in st.session_state:
                    st.session_state["live_trends"] = get_trending_topics(12)

                for trend in st.session_state["live_trends"]:
                    if st.button(
                        f"{trend['category']}  {trend['title'][:55]}{'…' if len(trend['title'])>55 else ''}",
                        use_container_width=True,
                        key=f"trend_{trend['title'][:30]}",
                    ):
                        st.session_state.topic = trend["title"]
                        st.rerun()

            with tab_presets:
                for cat, items in PRESET_CATEGORIES.items():
                    with st.expander(cat):
                        for item in items:
                            if st.button(item, key=f"preset_{item[:25]}", use_container_width=True):
                                st.session_state.topic = item
                                st.rerun()

        # ── Platform & format ──────────────────────────────────────────────
        st.markdown("#### 📱 Platforms & Format")
        platforms_selected = st.multiselect(
            "Target Platforms",
            list(PLATFORM_FORMATS.keys()),
            default=["Instagram", "X / Twitter"],
            label_visibility="collapsed",
        )
        primary_platform = platforms_selected[0] if platforms_selected else "Instagram"

        col_style, col_tone = st.columns(2)
        style_choice = col_style.selectbox("Visual Style", list(STYLE_PRESETS.keys()), index=0)
        tone_choice = col_tone.selectbox("Tone & Mood", list(TONE_PRESETS.keys()), index=0)

        content_type = st.radio(
            "Content Type",
            ["📸 Image", "🎬 Video", "🖼️ Carousel (3 images)"],
            horizontal=True,
        )

        # ── Brand settings ────────────────────────────────────────────────
        with st.expander("🏷️ Brand Settings (optional)"):
            brand_name = st.text_input("Brand / Creator Name", placeholder="@YourBrand")
            brand_voice = st.text_input(
                "Brand Voice", placeholder="Bold, witty, tech-forward"
            )
            brand_colors = st.text_input("Brand Colors", placeholder="Purple, Gold, White")
            cta_text = st.text_input("Call to Action", placeholder="Shop now · Follow · Learn more")

        extra_context = st.text_area(
            "Additional context (optional)",
            placeholder="Any specific details, hooks, or requirements...",
            height=80,
        )

        # ── GENERATE button ────────────────────────────────────────────────
        generate_btn = st.button(
            "⚡ Generate Content",
            type="primary",
            use_container_width=True,
            disabled=not st.session_state.topic,
        )

    # ── Right panel — results ──────────────────────────────────────────────
    with right:
        if generate_btn and st.session_state.topic:
            topic = st.session_state.topic

            # ── Build prompts ──────────────────────────────────────────────
            img_prompt = build_image_prompt(
                topic, primary_platform, style_choice, tone_choice, extra_context
            )
            vid_prompt = build_video_prompt(
                topic, primary_platform, style_choice, tone_choice, extra_context=extra_context
            )

            # ── Generate caption + hashtags via Claude ─────────────────────
            with st.spinner("🤖 Claude is writing your caption & hashtags…"):
                content = generate_caption_and_hashtags(
                    topic=topic,
                    platform=primary_platform,
                    tone=tone_choice,
                    brand_voice=brand_voice if "brand_voice" in dir() else "",
                    api_key=anthropic_key,
                )
                st.session_state.generated_caption = content.get("caption", "")
                st.session_state.generated_hashtags = content.get("hashtags", [])
                st.session_state.generated_cta = content.get("cta", "")
                st.session_state.generated_script = content.get("script", "")
                st.session_state.generated_hook = content.get("hook", "")

            # ── Generate image via Stability AI ───────────────────────────
            if "Image" in content_type or "Carousel" in content_type:
                with st.spinner("🎨 Generating image with Stability AI…"):
                    img_bytes = generate_image_stability(
                        prompt=img_prompt, api_key=stability_key
                    )
                    if img_bytes:
                        st.session_state.image_bytes = img_bytes
                    else:
                        st.session_state.image_bytes = None

            # ── Generate video via Replicate ───────────────────────────────
            if "Video" in content_type:
                with st.spinner("🎬 Submitting video job to Replicate (may take 60–120s)…"):
                    vid_url = generate_video_replicate(
                        prompt=vid_prompt, api_key=replicate_key
                    )
                    st.session_state.video_url = vid_url

        # ── Display results ────────────────────────────────────────────────
        if st.session_state.generated_caption:
            st.markdown("#### 📝 Generated Content")

            # Hook
            if st.session_state.generated_hook:
                st.info(f"**🪝 Hook:** {st.session_state.generated_hook}")

            # Caption
            caption_val = st.text_area(
                "Caption",
                value=st.session_state.generated_caption,
                height=150,
                key="caption_editor",
            )
            st.session_state.generated_caption = caption_val

            # Hashtags
            if st.session_state.generated_hashtags:
                hashtag_str = " ".join(
                    f"#{h}" for h in st.session_state.generated_hashtags
                )
                st.caption(f"**Hashtags:** {hashtag_str}")

            # CTA
            if st.session_state.generated_cta:
                st.success(f"**CTA:** {st.session_state.generated_cta}")

            # Script
            if st.session_state.generated_script:
                with st.expander("🎙️ Video Script / Voiceover"):
                    st.write(st.session_state.generated_script)

            # Copy buttons
            c1, c2 = st.columns(2)
            full_post = (
                st.session_state.generated_caption
                + "\n\n"
                + " ".join(f"#{h}" for h in st.session_state.generated_hashtags)
                + "\n"
                + st.session_state.generated_cta
            )
            c1.download_button(
                "⬇️ Download Caption",
                full_post,
                "caption.txt",
                use_container_width=True,
            )
            if c2.button("📋 Copy to Clipboard", use_container_width=True):
                st.toast("Caption copied! ✅")

        # ── Media preview ──────────────────────────────────────────────────
        if st.session_state.image_bytes:
            st.markdown("#### 🖼️ Generated Image")
            img = Image.open(io.BytesIO(st.session_state.image_bytes))
            st.image(img, use_container_width=True)
            st.download_button(
                "⬇️ Download Image",
                st.session_state.image_bytes,
                "social_content.png",
                "image/png",
                use_container_width=True,
            )
        elif st.session_state.image_bytes is None and st.session_state.generated_caption:
            st.info(
                "💡 **No image generated yet.** Add a Stability AI key to auto-generate images, "
                "or use the QuickFrame Studio tab to create professional video content.",
                icon="🎨",
            )

        if st.session_state.video_url:
            st.markdown("#### 🎬 Generated Video")
            st.video(st.session_state.video_url)
            st.download_button(
                "⬇️ Download Video URL",
                st.session_state.video_url,
                "video_url.txt",
                use_container_width=True,
            )

# ══════════════════════════════════════════════════
# TAB 2 — QUICKFRAME STUDIO
# ══════════════════════════════════════════════════
with tab_studio:
    st.markdown("#### 🎨 QuickFrame AI — Professional Video Studio")

    # Auto-generate brief from current topic
    if st.session_state.topic:
        brief = build_quickframe_brief(
            topic=st.session_state.topic,
            platform=list(PLATFORM_FORMATS.keys())[0],
            style=quick_style,
            tone=quick_tone,
            brand_name="",
            cta="",
        )

        st.markdown("##### 📋 Your QuickFrame Brief")
        st.markdown(
            "<small style='color:#94a3b8'>Copy these into QuickFrame AI to generate studio-quality video in minutes:</small>",
            unsafe_allow_html=True,
        )

        col_brief1, col_brief2 = st.columns(2)
        with col_brief1:
            st.markdown(
                f"""<div class="content-card">
                <strong>🎯 Script Prompt</strong><br>
                <span style='color:#e2e8f0'>{brief['script_prompt']}</span>
            </div>""",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"""<div class="content-card">
                <strong>🎨 Visual Style</strong> — {brief['style']}<br>
                <strong>🎭 Tone</strong> — {brief['tone']}<br>
                <strong>📢 CTA</strong> — {brief['cta']}
            </div>""",
                unsafe_allow_html=True,
            )

        with col_brief2:
            st.markdown(
                f"""<div class="content-card">
                <strong>📱 Platform</strong> — {brief['platform']}<br>
                <strong>🎯 Topic</strong> — {brief['topic']}
            </div>""",
                unsafe_allow_html=True,
            )
            if st.session_state.generated_script:
                st.markdown(
                    f"""<div class="content-card">
                    <strong>🎙️ Voiceover Script</strong><br>
                    <span style='color:#c4b5fd; font-style:italic'>{st.session_state.generated_script}</span>
                </div>""",
                    unsafe_allow_html=True,
                )

        st.markdown("---")

    # ── Launch QuickFrame button + embedded iframe ─────────────────────────
    qf_col1, qf_col2, qf_col3 = st.columns([1, 2, 1])
    with qf_col2:
        st.link_button(
            "🚀 Open QuickFrame AI Studio",
            "https://ai.quickframe.com",
            use_container_width=True,
            type="primary",
        )

    st.markdown(
        """
<div class="qf-container" style="height:700px; display:flex; align-items:center; justify-content:center;
     background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 100%);">
    <div style="text-align:center;">
        <div style="font-size:4rem; margin-bottom:1rem;">🎬</div>
        <h3 style="color:#a78bfa; margin:0">QuickFrame AI Studio</h3>
        <p style="color:#64748b; max-width:400px; margin:0.75rem auto">
            Click the button above to open QuickFrame AI in a new tab.<br>
            Use the brief generated on the left to create your video in minutes.
        </p>
        <div style="margin-top:1.5rem; display:flex; gap:1rem; justify-content:center; flex-wrap:wrap">
            <span style="background:#1e0a3c; border:1px solid #7c3aed44; border-radius:20px;
                  padding:0.3rem 1rem; color:#c4b5fd; font-size:0.85rem">✨ AI Script Generation</span>
            <span style="background:#1e0a3c; border:1px solid #7c3aed44; border-radius:20px;
                  padding:0.3rem 1rem; color:#c4b5fd; font-size:0.85rem">🎙️ AI Voiceover</span>
            <span style="background:#1e0a3c; border:1px solid #7c3aed44; border-radius:20px;
                  padding:0.3rem 1rem; color:#c4b5fd; font-size:0.85rem">🎞️ Generative Footage</span>
            <span style="background:#1e0a3c; border:1px solid #7c3aed44; border-radius:20px;
                  padding:0.3rem 1rem; color:#c4b5fd; font-size:0.85rem">📤 Publish to Meta · TikTok</span>
        </div>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── Platform spec reference ────────────────────────────────────────────
    st.markdown("---")
    st.markdown("##### 📐 Platform Video Specifications")
    spec_cols = st.columns(3)
    for i, (platform, specs) in enumerate(PLATFORM_FORMATS.items()):
        with spec_cols[i % 3]:
            st.markdown(
                f"""<div class="content-card">
                <strong>{platform}</strong><br>
                <small style='color:#64748b'>
                Video: {specs['video_ratio']} · Image: {specs['image_ratio']}<br>
                Caption: {specs['max_caption']:,} chars · #{specs['hashtag_limit']} hashtags<br>
                🕐 Best: {', '.join(specs['best_times'][:2])}
                </small>
            </div>""",
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════════
# TAB 3 — PUBLISH
# ══════════════════════════════════════════════════
with tab_publish:
    st.markdown("#### 🚀 Publish to Social Platforms")

    if not st.session_state.generated_caption:
        st.info(
            "👈 Go to the **Create** tab first to generate content, then come back here to publish.",
            icon="✨",
        )
    else:
        # ── Final caption preview + edit ───────────────────────────────────
        pub_col1, pub_col2 = st.columns([1.2, 0.8])
        with pub_col1:
            st.markdown("##### 📝 Final Caption")
            final_caption = st.text_area(
                "Edit before posting",
                value=st.session_state.generated_caption
                + "\n\n"
                + " ".join(f"#{h}" for h in st.session_state.generated_hashtags),
                height=200,
                label_visibility="collapsed",
            )

            # ── Platform selection ─────────────────────────────────────────
            st.markdown("##### 📱 Select Platforms to Post")
            post_to = {}
            p_cols = st.columns(3)
            platforms_list = list(PLATFORM_FORMATS.keys())
            for i, p in enumerate(platforms_list):
                post_to[p] = p_cols[i % 3].checkbox(p, value=(i < 2))

            # ── Image upload / use generated ───────────────────────────────
            st.markdown("##### 🖼️ Media")
            media_option = st.radio(
                "Media source",
                ["Use generated image", "Upload my own", "No image"],
                horizontal=True,
            )
            upload_bytes = None
            if media_option == "Upload my own":
                uploaded = st.file_uploader(
                    "Upload image", type=["png", "jpg", "jpeg", "webp"]
                )
                if uploaded:
                    upload_bytes = uploaded.read()
            elif media_option == "Use generated image":
                upload_bytes = st.session_state.image_bytes

            # ── POST button ────────────────────────────────────────────────
            if st.button("🚀 Publish Now", type="primary", use_container_width=True):
                results = {}
                selected = [p for p, v in post_to.items() if v]

                if not selected:
                    st.warning("Select at least one platform!")
                else:
                    creds = {
                        "twitter": {
                            "api_key": twitter_api_key,
                            "api_secret": twitter_api_secret,
                            "access_token": twitter_access_token,
                            "access_token_secret": twitter_access_secret,
                        },
                        "linkedin": {
                            "access_token": linkedin_token,
                            "person_urn": linkedin_urn,
                        },
                        "facebook": {
                            "access_token": fb_token,
                            "page_id": fb_page_id,
                        },
                        "instagram": {
                            "access_token": ig_token,
                            "ig_user_id": ig_user_id,
                        },
                    }

                    progress = st.progress(0)
                    status = st.status("Publishing…", expanded=True)

                    for idx, platform in enumerate(selected):
                        progress.progress((idx + 1) / len(selected))
                        status.write(f"Posting to {platform}…")

                        if platform == "X / Twitter":
                            results[platform] = post_to_twitter(
                                final_caption[:280], upload_bytes, creds["twitter"]
                            )
                        elif platform == "LinkedIn":
                            results[platform] = post_to_linkedin(
                                final_caption, upload_bytes, creds["linkedin"]
                            )
                        elif platform == "Facebook":
                            results[platform] = post_to_facebook(
                                final_caption, upload_bytes, creds["facebook"]
                            )
                        elif platform == "Instagram":
                            # IG API requires a public image URL
                            results[platform] = {
                                "success": False,
                                "url": "",
                                "error": "IG requires a public image URL — host your image first.",
                            }
                        else:
                            results[platform] = {
                                "success": False,
                                "url": "",
                                "error": f"{platform} posting requires manual upload via their app.",
                            }

                    status.update(label="Done!", state="complete")
                    progress.empty()

                    st.session_state.post_results = results
                    st.session_state.post_history.append(
                        {
                            "time": datetime.now().isoformat(),
                            "topic": st.session_state.topic,
                            "platforms": selected,
                            "results": results,
                        }
                    )
                    st.markdown(summarise_results(results))

        with pub_col2:
            st.markdown("##### 🖼️ Media Preview")
            if st.session_state.image_bytes:
                st.image(
                    Image.open(io.BytesIO(st.session_state.image_bytes)),
                    use_container_width=True,
                )
            elif st.session_state.video_url:
                st.video(st.session_state.video_url)
            else:
                st.markdown(
                    "<div style='height:250px; background:#1a1a2e; border:1px dashed #2d2d4a; "
                    "border-radius:12px; display:flex; align-items:center; justify-content:center; color:#475569'>"
                    "No media yet</div>",
                    unsafe_allow_html=True,
                )

            # ── Platform character count meters ────────────────────────────
            st.markdown("##### 📏 Character Counts")
            for p, v in post_to.items() if post_to else []:
                if v:
                    limit = PLATFORM_FORMATS[p]["max_caption"]
                    used = min(len(final_caption), limit)
                    pct = min(used / limit, 1.0)
                    color = "#10b981" if pct < 0.8 else ("#f59e0b" if pct < 0.95 else "#ef4444")
                    st.markdown(
                        f"<small><strong>{p}</strong>: {used:,}/{limit:,}</small>",
                        unsafe_allow_html=True,
                    )
                    st.progress(pct)

# ══════════════════════════════════════════════════
# TAB 4 — SCHEDULE
# ══════════════════════════════════════════════════
with tab_schedule:
    st.markdown("#### 📅 Schedule Posts")

    sched_col1, sched_col2 = st.columns(2)
    with sched_col1:
        sched_topic = st.text_input(
            "Topic", value=st.session_state.topic, key="sched_topic"
        )
        sched_platforms = st.multiselect(
            "Platforms", list(PLATFORM_FORMATS.keys()), default=["Instagram"]
        )
        sched_date = st.date_input("Date", min_value=datetime.today())
        sched_time = st.time_input("Time", value=datetime.now().replace(hour=9, minute=0, second=0))

    with sched_col2:
        sched_repeat = st.selectbox(
            "Repeat", ["Once", "Daily", "Weekly", "Mon/Wed/Fri", "Tue/Thu/Sat"]
        )
        sched_auto_generate = st.toggle("Auto-generate caption on post day", value=True)
        sched_style = st.selectbox("Style", list(STYLE_PRESETS.keys()), key="sched_style")
        sched_tone = st.selectbox("Tone", list(TONE_PRESETS.keys()), key="sched_tone")

    if st.button("➕ Add to Schedule", use_container_width=True):
        entry = {
            "id": len(st.session_state.scheduled_posts) + 1,
            "topic": sched_topic,
            "platforms": sched_platforms,
            "date": str(sched_date),
            "time": str(sched_time),
            "repeat": sched_repeat,
            "auto_generate": sched_auto_generate,
            "style": sched_style,
            "tone": sched_tone,
            "status": "Scheduled",
        }
        st.session_state.scheduled_posts.append(entry)
        st.success(f"✅ Scheduled: '{sched_topic}' for {sched_date} at {sched_time}")

    # ── Schedule table ─────────────────────────────────────────────────────
    if st.session_state.scheduled_posts:
        st.markdown("##### 📋 Upcoming Posts")
        import pandas as pd
        df = pd.DataFrame(st.session_state.scheduled_posts)
        df["platforms"] = df["platforms"].apply(lambda x: ", ".join(x))
        st.dataframe(
            df[["id", "topic", "platforms", "date", "time", "repeat", "status"]],
            use_container_width=True,
            hide_index=True,
        )

        if st.button("🗑️ Clear Schedule", type="secondary"):
            st.session_state.scheduled_posts = []
            st.rerun()

# ══════════════════════════════════════════════════
# TAB 5 — STRATEGY
# ══════════════════════════════════════════════════
with tab_strategy:
    st.markdown("#### 📈 AI Content Strategy")

    strat_topic = st.text_input(
        "Topic / Niche",
        value=st.session_state.topic or "Social media growth for small businesses",
        key="strat_topic",
    )
    strat_platforms = st.multiselect(
        "Target Platforms",
        list(PLATFORM_FORMATS.keys()),
        default=["Instagram", "TikTok", "LinkedIn"],
        key="strat_plats",
    )

    if st.button("🧠 Generate Strategy", type="primary", use_container_width=True):
        with st.spinner("Claude is building your strategy…"):
            strategy = generate_content_strategy(
                strat_topic, strat_platforms, api_key=anthropic_key
            )
            st.session_state.strategy_md = strategy

    if st.session_state.strategy_md:
        st.markdown(st.session_state.strategy_md)
        st.download_button(
            "⬇️ Download Strategy",
            st.session_state.strategy_md,
            "content_strategy.md",
            use_container_width=True,
        )

# ══════════════════════════════════════════════════
# TAB 6 — HISTORY
# ══════════════════════════════════════════════════
with tab_history:
    st.markdown("#### 📚 Post History")

    if not st.session_state.post_history:
        st.info("No posts yet — publish some content first!", icon="📭")
    else:
        for i, post in enumerate(reversed(st.session_state.post_history)):
            ts = datetime.fromisoformat(post["time"]).strftime("%b %d %Y · %H:%M")
            with st.expander(f"📌 {post['topic'][:60]} — {ts}"):
                st.write(f"**Platforms:** {', '.join(post['platforms'])}")
                if post.get("results"):
                    st.markdown(summarise_results(post["results"]))

        if st.button("🗑️ Clear History"):
            st.session_state.post_history = []
            st.rerun()

