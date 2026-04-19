from __future__ import annotations
import os, io, json, base64
import requests
from typing import Optional
from datetime import datetime


# ─────────────────────────────────────────────────────────────────────────────
# X / TWITTER
# ─────────────────────────────────────────────────────────────────────────────
def post_to_twitter(
    text: str,
    image_bytes: Optional[bytes] = None,
    credentials: dict = {},
) -> dict:
    """
    Posts a tweet with optional image. Returns {"success": bool, "url": str, "error": str}
    Credentials required: api_key, api_secret, access_token, access_token_secret
    """
    try:
        import tweepy

        c = credentials
        auth = tweepy.OAuth1UserHandler(
            c.get("api_key", os.getenv("TWITTER_API_KEY", "")),
            c.get("api_secret", os.getenv("TWITTER_API_SECRET", "")),
            c.get("access_token", os.getenv("TWITTER_ACCESS_TOKEN", "")),
            c.get("access_token_secret", os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")),
        )
        api_v1 = tweepy.API(auth)  # needed for media upload
        client = tweepy.Client(
            consumer_key=c.get("api_key", os.getenv("TWITTER_API_KEY", "")),
            consumer_secret=c.get("api_secret", os.getenv("TWITTER_API_SECRET", "")),
            access_token=c.get("access_token", os.getenv("TWITTER_ACCESS_TOKEN", "")),
            access_token_secret=c.get("access_token_secret", os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")),
        )

        media_ids = []
        if image_bytes:
            media = api_v1.media_upload(filename="content.png", file=io.BytesIO(image_bytes))
            media_ids.append(media.media_id)

        tweet = client.create_tweet(
            text=text[:280],
            media_ids=media_ids if media_ids else None,
        )
        tweet_id = tweet.data["id"]
        return {
            "success": True,
            "url": f"https://twitter.com/i/web/status/{tweet_id}",
            "id": tweet_id,
            "error": "",
        }
    except Exception as e:
        return {"success": False, "url": "", "id": "", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# LINKEDIN
# ─────────────────────────────────────────────────────────────────────────────
def post_to_linkedin(
    text: str,
    image_bytes: Optional[bytes] = None,
    credentials: dict = {},
) -> dict:
    """
    Posts to LinkedIn. Requires: access_token, person_urn (urn:li:person:XXXX)
    """
    access_token = credentials.get("access_token", os.getenv("LINKEDIN_ACCESS_TOKEN", ""))
    person_urn = credentials.get("person_urn", os.getenv("LINKEDIN_PERSON_URN", ""))

    if not access_token or not person_urn:
        return {"success": False, "url": "", "error": "Missing LinkedIn credentials"}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0",
    }

    try:
        media_asset = None
        if image_bytes:
            # Step 1: register upload
            reg_resp = requests.post(
                "https://api.linkedin.com/v2/assets?action=registerUpload",
                headers=headers,
                json={
                    "registerUploadRequest": {
                        "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                        "owner": person_urn,
                        "serviceRelationships": [
                            {"relationshipType": "OWNER", "identifier": "urn:li:userGeneratedContent"}
                        ],
                    }
                },
                timeout=30,
            )
            reg_data = reg_resp.json()
            upload_url = reg_data["value"]["uploadMechanism"][
                "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
            ]["uploadUrl"]
            media_asset = reg_data["value"]["asset"]

            # Step 2: upload image bytes
            requests.put(
                upload_url,
                headers={"Authorization": f"Bearer {access_token}"},
                data=image_bytes,
                timeout=60,
            )

        # Step 3: create post
        post_body: dict = {
            "author": person_urn,
            "lifecycleState": "PUBLISHED",
            "specificContent": {
                "com.linkedin.ugc.ShareContent": {
                    "shareCommentary": {"text": text[:3000]},
                    "shareMediaCategory": "IMAGE" if media_asset else "NONE",
                    **(
                        {
                            "media": [
                                {
                                    "status": "READY",
                                    "media": media_asset,
                                }
                            ]
                        }
                        if media_asset
                        else {}
                    ),
                }
            },
            "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"},
        }

        resp = requests.post(
            "https://api.linkedin.com/v2/ugcPosts",
            headers=headers,
            json=post_body,
            timeout=30,
        )
        resp.raise_for_status()
        post_id = resp.headers.get("x-restli-id", "")
        return {
            "success": True,
            "url": f"https://www.linkedin.com/feed/update/{post_id}",
            "id": post_id,
            "error": "",
        }
    except Exception as e:
        return {"success": False, "url": "", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# FACEBOOK / INSTAGRAM (via Meta Graph API)
# ─────────────────────────────────────────────────────────────────────────────
def post_to_facebook(
    text: str,
    image_bytes: Optional[bytes] = None,
    credentials: dict = {},
) -> dict:
    access_token = credentials.get("access_token", os.getenv("FACEBOOK_ACCESS_TOKEN", ""))
    page_id = credentials.get("page_id", os.getenv("FACEBOOK_PAGE_ID", ""))

    if not access_token or not page_id:
        return {"success": False, "url": "", "error": "Missing Facebook credentials"}

    try:
        if image_bytes:
            resp = requests.post(
                f"https://graph.facebook.com/{page_id}/photos",
                data={"message": text, "access_token": access_token},
                files={"source": ("content.png", io.BytesIO(image_bytes), "image/png")},
                timeout=60,
            )
        else:
            resp = requests.post(
                f"https://graph.facebook.com/{page_id}/feed",
                data={"message": text, "access_token": access_token},
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        post_id = data.get("id", "")
        return {
            "success": True,
            "url": f"https://www.facebook.com/{post_id}",
            "id": post_id,
            "error": "",
        }
    except Exception as e:
        return {"success": False, "url": "", "error": str(e)}


def post_to_instagram(
    caption: str,
    image_url: str,          # must be a public URL for IG API
    credentials: dict = {},
) -> dict:
    access_token = credentials.get("access_token", os.getenv("INSTAGRAM_ACCESS_TOKEN", ""))
    ig_user_id = credentials.get("ig_user_id", os.getenv("INSTAGRAM_USER_ID", ""))

    if not access_token or not ig_user_id:
        return {"success": False, "url": "", "error": "Missing Instagram credentials"}

    try:
        # Step 1: create container
        container_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media",
            data={
                "image_url": image_url,
                "caption": caption[:2200],
                "access_token": access_token,
            },
            timeout=30,
        )
        container_resp.raise_for_status()
        container_id = container_resp.json()["id"]

        # Step 2: publish
        pub_resp = requests.post(
            f"https://graph.facebook.com/v19.0/{ig_user_id}/media_publish",
            data={"creation_id": container_id, "access_token": access_token},
            timeout=30,
        )
        pub_resp.raise_for_status()
        media_id = pub_resp.json()["id"]

        return {
            "success": True,
            "url": f"https://www.instagram.com/p/{media_id}/",
            "id": media_id,
            "error": "",
        }
    except Exception as e:
        return {"success": False, "url": "", "error": str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# POSTING RESULT SUMMARY
# ─────────────────────────────────────────────────────────────────────────────
def summarise_results(results: dict[str, dict]) -> str:
    lines = [f"**📊 Posting Results — {datetime.now().strftime('%H:%M %Z')}**\n"]
    for platform, res in results.items():
        icon = "✅" if res.get("success") else "❌"
        line = f"{icon} **{platform}**: "
        if res.get("success"):
            line += f"[View Post]({res.get('url', '#')})"
        else:
            line += f"Failed — {res.get('error', 'Unknown error')}"
        lines.append(line)
    return "\n".join(lines)

