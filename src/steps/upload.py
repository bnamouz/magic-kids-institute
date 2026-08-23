"""Step 6: upload the finished MP4 to YouTube as a Short."""
from __future__ import annotations
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from .. import config

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _service():
    creds = None
    if config.YT_TOKEN_FILE.exists():
        creds = Credentials.from_authorized_user_file(str(config.YT_TOKEN_FILE), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(config.YT_CLIENT_SECRETS), SCOPES
            )
            creds = flow.run_local_server(port=8765)
        config.YT_TOKEN_FILE.write_text(creds.to_json())
    return build("youtube", "v3", credentials=creds)


def upload_short(video_path: Path, title: str, description: str, hashtags: list[str]) -> str:
    yt = _service()
    tags_line = " ".join(hashtags)
    full_desc = (
        f"{description}\n\n"
        f"{tags_line}\n\n"
        f"🧠 CurioDrop — one tiny mind-drop a day.\n"
        f"Follow @CurioDropAI for a new curiosity every morning."
    )

    body = {
        "snippet": {
            "title": title[:100],
            "description": full_desc[:5000],
            "tags": [t.lstrip("#") for t in hashtags][:15],
            "categoryId": config.YT_CATEGORY_ID,
            "defaultLanguage": "en",
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
    return resp["id"]
