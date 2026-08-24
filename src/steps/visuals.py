"""Step 4: turn each scene into a short vertical motion clip via fal.ai.

Uses a cartoon/kids-book art direction — bright, cheerful, no realism,
enforced by prepending a strong style prefix to every image prompt.
"""
from __future__ import annotations
import asyncio, os, urllib.request
from pathlib import Path
import fal_client
from .. import config

os.environ["FAL_KEY"] = config.FAL_API_KEY

# Cartoon/kids-book art direction — bright, safe, playful
STYLE_PREFIX = (
    "children's picture-book illustration, cute cartoon style, "
    "warm rounded shapes, big friendly eyes, bright cheerful colors, "
    "soft daylight, purple #7B5BFF and yellow #FFD166 accents, "
    "playful, safe, Pixar-meets-Sesame-Street aesthetic, "
)
STYLE_SUFFIX = (
    ", vertical 9:16 composition, hyper-detailed, "
    "absolutely no text, no letters, no words, no watermark, "
    "no violence, no scary elements, no realistic gore"
)


def _download(url: str, out: Path) -> Path:
    urllib.request.urlretrieve(url, out)
    return out


async def _image(prompt: str, out: Path) -> Path:
    handler = await fal_client.submit_async(
        config.IMAGE_MODEL,
        arguments={
            "prompt": STYLE_PREFIX + prompt + STYLE_SUFFIX,
            "image_size": "portrait_16_9",
            "num_inference_steps": 4,
            "num_images": 1,
        },
    )
    res = await handler.get()
    return _download(res["images"][0]["url"], out)


async def _motion(image_path: Path, motion_prompt: str, seconds: int, out: Path) -> Path:
    with open(image_path, "rb") as f:
        data_url = await fal_client.upload_async(f.read(), "image/png")
    handler = await fal_client.submit_async(
        config.MOTION_MODEL,
        arguments={
            "image_url": data_url,
            "prompt": "gentle, playful, kid-friendly motion — " + motion_prompt,
            "duration": str(min(seconds, 5)),
            "aspect_ratio": "9:16",
        },
    )
    res = await handler.get()
    return _download(res["video"]["url"], out)


async def _one_scene(scene: dict, out_dir: Path) -> Path:
    img = out_dir / f"scene_{scene['id']:02d}.png"
    vid = out_dir / f"scene_{scene['id']:02d}.mp4"
    if not img.exists():
        await _image(scene["image_prompt"], img)
    if not vid.exists():
        await _motion(img, scene["motion_prompt"], int(scene["seconds"]), vid)
    return vid


async def _all(scenes: list[dict], out_dir: Path) -> list[Path]:
    return await asyncio.gather(*[_one_scene(s, out_dir) for s in scenes])


def render_scenes(scenes: list[dict], run_dir: Path) -> list[Path]:
    run_dir.mkdir(parents=True, exist_ok=True)
    return asyncio.run(_all(scenes, run_dir))
