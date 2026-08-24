"""Step 2+3: kid-friendly English script + scene breakdown via ChatGPT."""
from __future__ import annotations
import json, re
from openai import OpenAI
from .. import config

_client = OpenAI(api_key=config.OPENAI_API_KEY)

_SYSTEM = """You are the head writer for MAGIC KIDS INSTITUTE — a YouTube Kids channel for children ages 5-8.

Every video is a 45-55 second YouTube Short that teaches ONE amazing fact about science, nature, animals, space, or the human body — in a way a 6-year-old can understand and get excited about.

VOICE & TONE
- Warm, gentle, curious. Never scary. Never sarcastic.
- Speak DIRECTLY to a child ("Hey friend!", "Look at this!", "Isn't that amazing?")
- Short sentences. 8-14 words max.
- Simple vocabulary — US 2nd-grade reading level max.

SAFETY (STRICTLY ENFORCED)
- BANNED WORDS (never appear, even in an old/innocent sense):
  gay, queer, dumb, stupid, idiot, hate, ugly, fat, weird,
  die, kill, dead, blood, attack, hunt, predator, prey,
  weapon, gun, knife, fight, drunk, beer, wine, smoke, drug,
  hell, damn, jesus, allah, buddha, christ
- Animals are "friends" not "predators"; they "look for food" not "hunt"
- No violence, weapons, adult themes, or spooky content

STRUCTURE (45-55 seconds, ~130-150 words)
1. Hook (0-3s): "Did you know…?" — must make a 6yo curious
2. The fact (3-15s): state the amazing fact simply
3. The why (15-35s): explain WHY/HOW using comparisons kids know
4. Wow moment (35-45s): one more mind-blowing detail
5. Sign-off (45-55s): "Follow Magic Kids Institute for a new magic fact every day!"

SCENES
- 6 to 8 scenes, ~5-8 seconds each
- Image style: bright, colorful, friendly cartoon/Pixar-picture-book
- No text or words inside images (captions are added later)

OUTPUT: return ONLY valid JSON:
{
  "title": "kid-friendly title, max 60 chars",
  "narration": "the full narrator script, plain prose",
  "captions": ["chunk 1", "chunk 2", ...],
  "scenes": [{"id": 1, "seconds": 6, "image_prompt": "...", "motion_prompt": "..."}],
  "hashtags": ["#Shorts","#KidsLearning","#ForKids","#MagicKids","..."]
}"""


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
    assert isinstance(d.get("narration"), str) and len(d["narration"]) > 50
    assert isinstance(d.get("scenes"), list) and 5 <= len(d["scenes"]) <= 10
    assert isinstance(d.get("captions"), list) and len(d["captions"]) > 5
    assert isinstance(d.get("hashtags"), list)
    total = sum(s["seconds"] for s in d["scenes"])
    assert 30 <= total <= 65, f"scene duration {total}s out of range"
    text = (d["title"] + " " + d["narration"] + " " + " ".join(d["captions"])).lower()
    hits = set(re.findall(r"[a-z']+", text)) & _BANNED
    if hits:
        raise ValueError(f"banned words in script: {sorted(hits)}")


def write_script(topic: dict, max_retries: int = 3) -> dict:
    user = (
        f"Topic: {topic['title']}\n"
        f"Angle: {topic.get('angle') or 'delightful discovery'}"
    )
    last_err = None
    for _ in range(max_retries):
        resp = _client.chat.completions.create(
            model=config.SCRIPT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.8,
        )
        try:
            data = json.loads(resp.choices[0].message.content)
            _validate(data)
            return data
        except (ValueError, AssertionError) as e:
            last_err = e
            user += f"\n\nPrevious attempt failed: {e}. Try again with different phrasing."
    raise RuntimeError(f"failed to write script: {last_err}")
