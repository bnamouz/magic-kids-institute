"""Supabase client + schema helpers.

Tables (create via `docs/SETUP.md`):

    topics (
        id           uuid primary key default gen_random_uuid(),
        title        text not null,
        angle        text,
        used_at      timestamptz,
        created_at   timestamptz default now()
    )

    videos (
        id             uuid primary key default gen_random_uuid(),
        topic_id       uuid references topics(id),
        youtube_id     text,
        title          text,
        description    text,
        status         text,           -- draft | rendered | uploaded | failed
        error          text,
        cost_usd       numeric,
        created_at     timestamptz default now()
    )
"""
from supabase import create_client, Client
from . import config


def client() -> Client:
    return create_client(config.SUPABASE_URL, config.SUPABASE_KEY)


def next_topic() -> dict:
    """Pick the oldest unused topic."""
    sb = client()
    r = (
        sb.table("topics")
        .select("*")
        .is_("used_at", "null")
        .order("created_at")
        .limit(1)
        .execute()
    )
    if not r.data:
        raise RuntimeError("Topic queue empty — run `python -m src.seed_topics`.")
    return r.data[0]


def mark_topic_used(topic_id: str) -> None:
    client().table("topics").update({"used_at": "now()"}).eq("id", topic_id).execute()


def log_video(**fields) -> str:
    r = client().table("videos").insert(fields).execute()
    return r.data[0]["id"]


def update_video(video_id: str, **fields) -> None:
    client().table("videos").update(fields).eq("id", video_id).execute()
