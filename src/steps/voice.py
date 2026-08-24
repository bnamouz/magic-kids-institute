"""Step 5a: TTS narration + word-level timings via ElevenLabs.

Picks voice by language (EN uses a warm kid-friendly female,
AR uses a clear Arabic-optimized voice). Both use eleven_multilingual_v2.
"""
from __future__ import annotations
from pathlib import Path
import requests
from .. import config

API = "https://api.elevenlabs.io/v1"
HEADERS = {"xi-api-key": config.ELEVENLABS_API_KEY}


def _voice_id(language: str) -> str:
    return config.ELEVENLABS_VOICE_ID_AR if language == "ar" else config.ELEVENLABS_VOICE_ID_EN


def narrate(text: str, out_mp3: Path, language: str = "en") -> Path:
    r = requests.post(
        f"{API}/text-to-speech/{_voice_id(language)}?output_format=mp3_44100_128",
        headers={**HEADERS, "Content-Type": "application/json"},
        json={
            "text": text,
            "model_id": config.ELEVENLABS_MODEL,
            "voice_settings": {
                # slightly softer, warmer, more expressive for kids
                "stability": 0.60,
                "similarity_boost": 0.80,
                "style": 0.40,
                "use_speaker_boost": True,
            },
        },
        timeout=120,
    )
    r.raise_for_status()
    out_mp3.write_bytes(r.content)
    return out_mp3


def force_align(mp3: Path, transcript: str) -> list[dict]:
    """Return [{word, start, end}, ...] using ElevenLabs forced alignment.

    Works for both English and Arabic; ElevenLabs auto-detects.
    """
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
