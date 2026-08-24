"""Supabase client + schema helpers."""
from supabase import create_client, Client
from . import config


def client() -> Client:
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def next_topic(content_type: str) -> dict:
    """Pick the oldest unused topic for the given content_type ('fact' or 'song')."""
    sb = client()
    r = (
        sb.table("topics")
        .select("*")
        .eq("content_type", content_type)
        .is_("used_at", "null")
        .order("created_at")
        .limit(1)
        .execute()
    )
    if not r.data:
        raise RuntimeError(f"No unused {content_type} topics.")
    return r.data[0]


def mark_topic_used(topic_id: str) -> None:
    client().table("topics").update({"used_at": "now()"}).eq("id", topic_id).execute()


def log_video(**fields) -> str:
    r = client().table("videos").insert(fields).execute()
    return r.data[0]["id"]


def update_video(video_id: str, **fields) -> None:
    client().table("videos").update(fields).eq("id", video_id).execute()
