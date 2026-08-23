"""Step 2+3: script + scene breakdown via ChatGPT."""
from __future__ import annotations
import json
from openai import OpenAI
from .. import config

_client = OpenAI(api_key=config.OPENAI_API_KEY)

SYSTEM = """You are the head writer for CurioDrop — a faceless YouTube Shorts channel
that delivers one 55-second "did you know" curiosity drop per day.

House style:
- Warm, playful, kid-safe. Wonder over shock.
- Hook in the first 2 seconds ("Wait — did you know that…?").
- 3 beats: HOOK → REVEAL → PAYOFF (a surprising twist or takeaway).
- 130-150 words total (≈55 seconds at 165 wpm).
- No jargon. No slurs. No violence. No political takes.
- End with a soft CTA: "Follow for a new mind-drop every day."

Return STRICT JSON matching this schema:

{
  "title": "hook-style YouTube title, max 60 chars, no clickbait caps",
  "narration": "the full narrator script, plain prose, no stage directions",
  "captions": ["chunk 1", "chunk 2", ...],   // 2-5 word chunks, in order, aligned to narration
  "scenes": [
    {
      "id": 1,
      "seconds": 5,
      "image_prompt": "cinematic still, subject, environment, lighting, mood — no text, no logos",
      "motion_prompt": "short camera or subject motion — dolly in, slow parallax, gentle turn"
    },
    ... 6 to 8 scenes total, sum of seconds ≈ 55
  ],
  "hashtags": ["#Shorts","#DidYouKnow","..."]  // 6-10 tags
}
"""


def write_script(topic: dict) -> dict:
    user = f"Topic: {topic['title']}\nAngle: {topic.get('angle') or 'surprising, delightful'}"
    resp = _client.chat.completions.create(
        model=config.SCRIPT_MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": user},
        ],
        temperature=0.85,
    )
    data = json.loads(resp.choices[0].message.content)
    _validate(data)
    return data


def _validate(d: dict) -> None:
    assert isinstance(d.get("title"), str) and 0 < len(d["title"]) <= 100
    assert isinstance(d.get("narration"), str) and len(d["narration"]) > 200
    assert isinstance(d.get("scenes"), list) and 5 <= len(d["scenes"]) <= 10
    assert isinstance(d.get("captions"), list) and len(d["captions"]) > 5
    assert isinstance(d.get("hashtags"), list)
    total = sum(s["seconds"] for s in d["scenes"])
    assert 45 <= total <= 65, f"scene duration {total}s out of range"
