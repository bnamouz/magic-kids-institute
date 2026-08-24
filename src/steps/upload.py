"""Step 6: upload the finished MP4 to YouTube as a Short.

Every video is Made For Kids (COPPA). English-only channel.
Also uploads a custom thumbnail (best-effort; ignored if account not verified).
Comments are DISABLED on Made-For-Kids videos, so we don't post an auto-comment.
"""
from __future__ import annotations
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from .. import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service():
    creds = None
    if config.YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(config.YT_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            config.YT_TOKEN_FILE.write_text(creds.to_json())
        else:
            # Local OAuth only; on Railway the token file must already exist.
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.YT_CLIENT_SECRETS), SCOPES
            )
            creds = flow.run_local_server(port=8765)
            config.YT_TOKEN_FILE.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload_short(
    video_path: Path,
    title: str,
    description: str,
    hashtags: list[str],
    thumbnail_path: Path | None = None,
) -> str:
    yt = _service()
    tags_line = " ".join(hashtags)
    follow = f"Follow {config.BRAND_HANDLE} for a new magic moment every day."
    full_desc = (
        f"{description}\n\n"
        f"{tags_line}\n\n"
        f"{config.BRAND_NAME} - {config.BRAND_TAGLINE}\n"
        f"{follow}\n\n"
        f"SUBSCRIBE for a new magic fact and song every day!"
    )
    body = {
        "snippet": {
            "title": title[:100],
            "description": full_desc[:5000],
            "tags": [t.lstrip("#") for t in hashtags][:15],
            "categoryId": config.YT_CATEGORY_ID,
            "defaultLanguage": "en",
            "defaultAudioLanguage": "en",
        },
        "status": {
            "privacyStatus": config.YT_PRIVACY,
            "selfDeclaredMadeForKids": config.YT_MADE_FOR_KIDS,
        },
    }
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True, mimetype="video/mp4")
    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = None
    while resp is None:
        _, resp = req.next_chunk()
    video_id = resp["id"]

    # Best-effort thumbnail upload (requires channel verification)
    if thumbnail_path and thumbnail_path.exists():
        try:
            yt.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/png"),
            ).execute()
            print(f"[upload] custom thumbnail applied to {video_id}")
        except HttpError as e:
            # Common: 403 if channel unverified for custom thumbnails
            print(f"[upload] thumbnail upload skipped: {e.status_code} {e.reason}")

    return video_id
