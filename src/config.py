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
MOTION_MODEL = "fal-ai/kling-video/v2.1/standard/image-to-video"   # cost-effective motion

# --- Voice (ElevenLabs) ---
ELEVENLABS_API_KEY = os.environ["ELEVENLABS_API_KEY"]
# Warm kid-friendly English narrator (Bella)
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "pMsXgVXv3BLzUgSXRplE")
ELEVENLABS_MODEL = "eleven_multilingual_v2"
# Music model for songs
ELEVENLABS_MUSIC_MODEL = os.getenv("ELEVENLABS_MUSIC_MODEL", "music_v1")

# --- Supabase ---
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

# --- YouTube ---
YT_CLIENT_SECRETS = ROOT / "youtube_client_secret.json"
YT_TOKEN_FILE = ROOT / "youtube_token.json"
YT_CATEGORY_ID = "27"                    # Education
YT_PRIVACY = os.getenv("YT_PRIVACY", "public")
YT_MADE_FOR_KIDS = True                  # COPPA compliance

# --- Content mode ---
# "fact" (science short) | "song" (musical short)
CONTENT_TYPE = os.getenv("CONTENT_TYPE", "fact")

# --- Brand ---
BRAND_NAME = "Magic Kids Institute"
BRAND_HANDLE = "@MagicKidsInstitute"
BRAND_TAGLINE = "Learn something magical every day."
BRAND_COLOR = "#7B5BFF"                  # playful purple
BRAND_ACCENT = "#FFD166"                 # warm yellow
CAPTION_FONT = ASSETS / "captions" / "Baloo2-Bold.ttf"

# --- Mascot ---
MASCOT_NAME = "Lumi"
MASCOT_DESCRIPTION = (
    "Lumi is a cheerful glowing yellow lightbulb character with big friendly "
    "eyes, tiny rounded arms, rosy cheeks, and a purple base. Pixar-picture-book "
    "cartoon style. She sparkles when excited. She is the guide of Magic Kids Institute."
)

# --- Video specs ---
WIDTH, HEIGHT = 1080, 1920               # 9:16
FPS = 30
DURATION_SEC = 55                        # keep under 60s Shorts cap

# Explicit token path — Railway will provide it via a secret file mount
import os as _os
if _os.getenv("YT_TOKEN_PATH"):
    YT_TOKEN_FILE = Path(_os.environ["YT_TOKEN_PATH"])
if _os.getenv("YT_CLIENT_SECRETS_PATH"):
    YT_CLIENT_SECRETS = Path(_os.environ["YT_CLIENT_SECRETS_PATH"])
