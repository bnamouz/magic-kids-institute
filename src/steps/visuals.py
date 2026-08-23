"""Step 4: turn each scene into a short vertical motion clip via fal.ai."""
from __future__ import annotations
import asyncio, os, tempfile, urllib.request
from pathlib import Path
import fal_client
from .. import config

os.environ["FAL_KEY"] = config.FAL_API_KEY


def _download(url: str, out: Path) -> Path:
    urllib.request.urlretrieve(url, out)
    return out


async def _image(prompt: str, out: Path) -> Path:
    """Generate a still — 9:16, cinematic."""
    handler = await fal_client.submit_async(
        config.IMAGE_MODEL,
        arguments={
            "prompt": (
                prompt +
                ", cinematic, soft golden light, shallow depth of field, "
                "vertical 9:16 composition, hyper-detailed, no text, no watermark"
            ),
            "image_size": "portrait_16_9",  # fal alias for 9:16
            "num_inference_steps": 4,
            "num_images": 1,
        },
    )
    res = await handler.get()
    return _download(res["images"][0]["url"], out)


async def _motion(image_path: Path, motion_prompt: str, seconds: int, out: Path) -> Path:
    """Animate still with Kling image-to-video."""
    with open(image_path, "rb") as f:
        data_url = await fal_client.upload_async(f.read(), "image/png")
    handler = await fal_client.submit_async(
        config.MOTION_MODEL,
        arguments={
            "image_url": data_url,
            "prompt": motion_prompt,
            "duration": str(min(seconds, 5)),   # Kling caps at 5s
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
    """Sync entry point."""
    run_dir.mkdir(parents=True, exist_ok=True)
    return asyncio.run(_all(scenes, run_dir))
