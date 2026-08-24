"""Song writer + composer.

Uses GPT-4o-mini to write kid-safe lyrics with structure.
Uses ElevenLabs Music API to produce the sung audio with backing track.
"""
from __future__ import annotations
import json, requests
from pathlib import Path
from openai import OpenAI
from .. import config

_client = OpenAI(api_key=config.OPENAI_API_KEY)

_SYSTEM = """You are the head songwriter for MAGIC KIDS INSTITUTE — a YouTube Kids channel for ages 5-8.

The channel mascot is LUMI: a cheerful glowing yellow lightbulb character with big friendly eyes, tiny rounded arms, and a purple base. Lumi sings, dances, and guides children through fun learning songs. Every song either features Lumi directly or is hosted by Lumi.

Write an ORIGINAL song that has never existed. Do NOT reference or adapt existing songs like "Old MacDonald", "Wheels on the Bus", "Twinkle Twinkle", "ABC Song", or any copyrighted material. Melody hints and lyrics must be 100% original.

SAFETY RULES (STRICTLY ENFORCED)
- Warm, cheerful, uplifting tone. Never scary.
- Simple vocabulary — US 2nd-grade reading level (ages 5-8)
- Sad feelings ARE allowed IF the song resolves to comfort/hope by the end
- BANNED WORDS (never appear, even in an old/innocent sense — kids and parents will misread them):
  gay, queer, straight (as identity), dumb, stupid, idiot, hate, ugly, fat, weird,
  die, kill, dead, blood, attack, hunt, predator, prey, weapon, gun, knife, fight,
  drunk, beer, wine, smoke, drug,
  hell, damn, god, jesus, allah, buddha, church, mosque, temple,
  boy/girl gender jokes, body-shape jokes
- All animals are "friends"; all adventures end happily
- No real brand names, celebrities, or living people
- Do NOT rhyme by reaching for archaic/dated words — modern kid English only
- If a rhyme is hard, change the whole line rather than force a banned/awkward word

SONG STRUCTURE (30-45 seconds total; ~50-70 syllables of lyrics)
- Verse 1 (2 lines, rhyming AABB or ABAB)
- Chorus (2 lines with a fun repetitive hook that kids can sing back)
- Verse 2 (2 lines, extending the story)
- Chorus (repeat — same lines exactly)

VISUAL SCENES
6 to 8 scenes, ~5-6 seconds each, in bright cartoon/Pixar picture-book style.
Lumi should appear in most scenes. Style prompt hints go inside image_prompt.

MUSIC STYLE PROMPT for the audio model:
Describe: tempo (upbeat/gentle/playful), instruments (ukulele/glockenspiel/xylophone/toy piano/light drums/hand claps), mood (joyful/silly/dreamy), a female child-friendly singer.

OUTPUT — return ONLY valid JSON:
{
  "title": "song title, 3-8 words, kid-friendly",
  "lyrics": "the FULL lyric text with line breaks and structure labels ([Verse 1], [Chorus], [Verse 2], [Chorus])",
  "music_prompt": "one-paragraph description for the music model, including tempo, instruments, mood, and the singer style",
  "captions": ["line 1 of lyrics", "line 2 of lyrics", ...] (one caption per lyric line, chorus repeated),
  "scenes": [
    {"id": 1, "seconds": 5, "image_prompt": "...", "motion_prompt": "..."}
  ],
  "hashtags": ["#Shorts","#KidsSongs","#ForKids","#MagicKids","#Lumi","..."]
}"""


def write_song(topic: dict, max_retries: int = 3) -> dict:
    """Generate lyrics + music prompt + scenes for a song.
    Retries automatically if banned words appear.
    """
    user = (
        f"Song topic: {topic['title']}\n"
        f"Angle: {topic.get('angle') or ''}\n"
        f"Category tag: {(topic.get('tags') or ['general'])[0]}"
    )
    last_err: Exception | None = None
    for attempt in range(max_retries):
        resp = _client.chat.completions.create(
            model=config.SCRIPT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.85,
        )
        try:
            data = json.loads(resp.choices[0].message.content)
            _validate(data)
            return data
        except (ValueError, AssertionError) as e:
            last_err = e
            user += f"\n\nPrevious attempt failed: {e}. Try again with different phrasing."
    raise RuntimeError(f"failed to write song after {max_retries} attempts: {last_err}")


_BANNED = {
    "gay", "queer", "dumb", "stupid", "idiot", "hate", "ugly", "fat", "weird",
    "die", "dying", "kill", "killed", "killing", "dead", "death",
    "blood", "bloody", "attack", "hunt", "hunting", "predator", "prey",
    "weapon", "gun", "guns", "knife", "fight", "fighting",
    "drunk", "beer", "wine", "smoke", "smoking", "drug", "drugs",
    "hell", "damn", "jesus", "allah", "buddha", "christ",
}


def _validate(d: dict) -> None:
    assert isinstance(d.get("title"), str) and 0 < len(d["title"]) <= 100
    assert isinstance(d.get("lyrics"), str) and len(d["lyrics"]) > 40
    assert isinstance(d.get("music_prompt"), str) and len(d["music_prompt"]) > 20
    assert isinstance(d.get("scenes"), list) and 5 <= len(d["scenes"]) <= 10
    assert isinstance(d.get("captions"), list) and len(d["captions"]) >= 4
    assert isinstance(d.get("hashtags"), list)
    total = sum(s["seconds"] for s in d["scenes"])
    assert 25 <= total <= 60, f"scene duration {total}s out of range"
    # Banned-word check on lyrics + captions + title
    import re
    text = (d["title"] + " " + d["lyrics"] + " " + " ".join(d["captions"])).lower()
    tokens = set(re.findall(r"[a-z']+", text))
    hits = tokens & _BANNED
    if hits:
        raise ValueError(f"banned words in lyrics: {sorted(hits)}")


# --- ElevenLabs Music API -------------------------------------------------

_MUSIC_ENDPOINT = "https://api.elevenlabs.io/v1/music/compose"


def compose_song(lyrics: str, music_prompt: str, out_mp3: Path, target_seconds: int = 40) -> Path:
    """Generate a sung song with backing music via ElevenLabs Music."""
    body = {
        "prompt": (
            f"{music_prompt}\n\n"
            "Lyrics to sing (must be sung clearly with correct pronunciation):\n"
            f"{lyrics}"
        ),
        "music_length_ms": target_seconds * 1000,
    }
    r = requests.post(
        _MUSIC_ENDPOINT,
        headers={
            "xi-api-key": config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
        json=body,
        timeout=300,
    )
    r.raise_for_status()
    out_mp3.write_bytes(r.content)
    return out_mp3
