"""Central config — all env vars in one place."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

# --- LLM ---
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
SCRIPT_MODEL = os.getenv("SCRIPT_MODEL", "gpt-4o-mini")

# --- Visuals (fal.ai) ---
FAL_API_KEY = os.environ["FAL_API_KEY"]
IMAGE_MODEL = "fal-ai/flux/schnell"                                # cheap, fast
MOTION_MODEL = "fal-ai/kling-video/v1.5/standard/image-to-video"   # gentle motion

# --- Voice (ElevenLabs) ---
ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
# Kid-friendly voices:
#   English narrator: "Bella" — soft, warm, kid-friendly female (pMsXgVXv3BLzUgSXRplE)
#   Arabic narrator: "Sarah" — clear, gentle, works well in Arabic (EXAVITQu4vr4xnSDxMaL)
# Override in .env with ELEVENLABS_VOICE_ID_EN / ELEVENLABS_VOICE_ID_AR.
ELEVENLABS_VOICE_ID_EN = os.getenv("ELEVENLABS_VOICE_ID_EN", "pMsXgVXv3BLzUgSXRplE")
ELEVENLABS_VOICE_ID_AR = os.getenv("ELEVENLABS_VOICE_ID_AR", "EXAVITQu4vr4xnSDxMaL")
ELEVENLABS_MODEL = "eleven_multilingual_v2"  # supports both English + Arabic

# --- Supabase (topic queue + logs) ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

# --- YouTube ---
YT_CLIENT_SECRETS = ROOT / "youtube_client_secret.json"
YT_TOKEN_FILE = ROOT / "youtube_token.json"
YT_CATEGORY_ID = "27"                    # Education (best fit for kids edu Shorts)
YT_PRIVACY = os.getenv("YT_PRIVACY", "public")   # public | unlisted | private
YT_MADE_FOR_KIDS = True                  # Made For Kids compliance (COPPA)

# --- Language rotation ---
# Which language to produce per invocation.
# Accepts: "en", "ar", or "auto" (alternates by parity of the day-of-year)
RUN_LANGUAGE = os.getenv("RUN_LANGUAGE", "auto")

# --- Brand ---
BRAND_NAME = "Magic Kids Institute"
BRAND_HANDLE = "@MagicKidsInstitute"
BRAND_TAGLINE_EN = "One magic fact every day."
BRAND_TAGLINE_AR = "حقيقة سحرية كل يوم."
BRAND_COLOR = "#7B5BFF"                  # playful purple
BRAND_ACCENT = "#FFD166"                 # warm yellow
CAPTION_FONT_EN = ASSETS / "captions" / "Baloo2-Bold.ttf"
CAPTION_FONT_AR = ASSETS / "captions" / "Cairo-Bold.ttf"

# --- Video specs ---
WIDTH, HEIGHT = 1080, 1920               # 9:16
FPS = 30
DURATION_SEC = 55                        # keep under 60s YouTube Shorts cap
