# Magic Kids Institute — Daily YouTube Shorts (EN + AR)

Fully automated YouTube Kids Shorts channel for children ages 5-8.
Every day the pipeline picks a topic from the queue, writes a kid-safe
script, renders 6-8 cartoon scenes with AI, adds voiceover + captions,
and uploads a Made-For-Kids YouTube Short.

Runs **twice per day** — one English Short in the morning, one Arabic
Short in the evening. Cost ~$0.60 per video.

## What's inside

- **Language:** English + Arabic (Modern Standard, kid-friendly)
- **Age target:** 5-8 (safety-hardened script prompt, COPPA-compliant)
- **Style:** Cartoon/picture-book aesthetic — bright, warm, Pixar-meets-Sesame-Street
- **Duration:** 45-55 seconds per Short
- **Channel:** [@MagicKidsInstitute](https://youtube.com/@MagicKidsInstitute)

## Pipeline

1. Pick unused topic from Supabase `topics` table (230 pre-seeded facts)
2. GPT-4o-mini writes a kid-safe script in the chosen language
3. fal.ai Flux renders 6-8 cartoon-style scene images
4. fal.ai Kling adds gentle motion to each scene
5. ElevenLabs generates warm kid-friendly narration + word timings
6. FFmpeg composes video with music, captions (RTL-safe for Arabic), and branding
7. YouTube Data API uploads as a Made-For-Kids Short

## Setup

See [`docs/SETUP.md`](docs/SETUP.md) for step-by-step instructions.

## Brand

- **Name:** Magic Kids Institute
- **Handle:** `@MagicKidsInstitute`
- **Tagline (EN):** One magic fact every day.
- **Tagline (AR):** حقيقة سحرية كل يوم.
- **Colors:** Purple `#7B5BFF` + Yellow `#FFD166`
- **Fonts:** Baloo 2 Bold (English), Cairo Bold (Arabic)

## Structure

```
curio-drop-ai/
├─ src/
│  ├─ config.py           # env vars + brand constants
│  ├─ db.py               # Supabase helpers
│  ├─ main.py             # orchestrator (one video per invocation)
│  └─ steps/
│     ├─ script.py        # kid-safe GPT prompt EN+AR
│     ├─ visuals.py       # cartoon-styled image + Kling motion
│     ├─ voice.py         # ElevenLabs kid-friendly voice EN+AR
│     ├─ compose.py       # FFmpeg — RTL captions + music
│     └─ upload.py        # YouTube API, Made For Kids = true
├─ prompts/
│  ├─ script_system.md    # editorial system prompt reference
│  └─ topic_ideas.txt     # 230 kid-safe curiosity topics
├─ assets/                # avatar, banner, captions, music
├─ docs/                  # SETUP.md, BRAND.md, CONTENT_STRATEGY.md
├─ Dockerfile
├─ railway.json
├─ requirements.txt
└─ .env.example
```
