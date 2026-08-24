"""Generate a bold YouTube Shorts thumbnail (1080x1920) using gpt-image."""
from __future__ import annotations
from pathlib import Path
import base64, requests
from .. import config


def make_thumbnail(topic: dict, out: Path) -> Path:
    """Generate a vertical 1080x1920 thumbnail with Lumi + big keyword text.

    Uses OpenAI images API directly (gpt-image-1).
    """
    keyword = _keyword(topic["title"])
    prompt = (
        f"YouTube Shorts thumbnail, 9:16 vertical. "
        f"Lumi the mascot (cheerful glowing yellow lightbulb with big smiley eyes, "
        f"rosy cheeks, tiny rounded arms, purple base, sparkles around her) fills "
        f"the left half of the frame, looking excited and pointing at HUGE bold "
        f"text on the right that reads: \"{keyword.upper()}\" in chunky bright "
        f"yellow letters with thick black outline and drop shadow. "
        f"Background: vibrant gradient (purple to pink to sky-blue) with cartoon "
        f"stars and confetti. Kid-friendly picture-book style, hyper-saturated "
        f"colors, high contrast, safe for kids. NO other words or letters "
        f"anywhere in the image except the one keyword. No small text, no logo."
    )

    r = requests.post(
        "https://api.openai.com/v1/images/generations",
        headers={
            "Authorization": f"Bearer {config.OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "gpt-image-1",
            "prompt": prompt,
            "size": "1024x1536",
            "quality": "medium",
            "n": 1,
        },
        timeout=120,
    )
    r.raise_for_status()
    b64 = r.json()["data"][0]["b64_json"]
    out.write_bytes(base64.b64decode(b64))
    return out


def _keyword(title: str) -> str:
    """Extract the most punchy 1-3 word phrase from the title."""
    stop = {"the", "a", "an", "of", "and", "or", "in", "on", "with", "for",
            "to", "how", "why", "what", "is", "are", "can", "your", "you",
            "did", "know", "that", "this"}
    words = [w.strip(".,!?:;\"'").upper() for w in title.split()]
    keep = [w for w in words if w and w.lower() not in stop]
    return " ".join(keep[:3]) if keep else "MAGIC"
