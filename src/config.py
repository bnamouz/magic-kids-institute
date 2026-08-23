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
IMAGE_MODEL = "fal-ai/flux/schnell"          # cheap, fast, cinematic
MOTION_MODEL = "fal-ai/kling-video/v1.5/standard/image-to-video"

# --- Voice (ElevenLabs) ---
ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")  # Rachel
ELEVENLABS_MODEL = "eleven_turbo_v2_5"

# --- Supabase (topic queue + logs) ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

# --- YouTube ---
YT_CLIENT_SECRETS = ROOT / "youtube_client_secret.json"
YT_TOKEN_FILE = ROOT / "youtube_token.json"
YT_CATEGORY_ID = "27"     # Education
YT_PRIVACY = os.getenv("YT_PRIVACY", "public")  # public | unlisted | private
YT_MADE_FOR_KIDS = False

# --- Brand ---
BRAND_NAME = "CurioDrop"
BRAND_TAGLINE = "One tiny mind-drop a day."
BRAND_COLOR = "#5B8CFF"   # soft blue-purple
CAPTION_FONT = ASSETS / "captions" / "Inter-Bold.ttf"

# --- Video specs ---
WIDTH, HEIGHT = 1080, 1920            # 9:16
FPS = 30
DURATION_SEC = 55                     # keep under 60s
