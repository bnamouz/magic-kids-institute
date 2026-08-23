"""Step 5a: TTS narration + word-level timings via ElevenLabs."""
from __future__ import annotations
from pathlib import Path
import requests
from .. import config

API = "https://api.elevenlabs.io/v1"
HEADERS = {"xi-api-key": config.ELEVENLABS_API_KEY}


def narrate(text: str, out_mp3: Path) -> Path:
    r = requests.post(
        f"{API}/text-to-speech/{config.ELEVENLABS_VOICE_ID}?output_format=mp3_44100_128",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": config.ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.85,
                "style": 0.35,
                "use_speaker_boost": True,
            },
        },
        timeout=120,
    )
    r.raise_for_status()
    out_mp3.write_bytes(r.content)
    return out_mp3


def force_align(mp3: Path, transcript: str) -> list[dict]:
    """Return [{word, start, end}, ...] using ElevenLabs forced alignment."""
    with open(mp3, "rb") as f:
        r = requests.post(
            f"{API}/forced-alignment",
            headers=HEADERS,
            files={"file": ("audio.mp3", f, "audio/mpeg")},
            data={"text": transcript},
            timeout=180,
        )
    r.raise_for_status()
    return r.json()["words"]
