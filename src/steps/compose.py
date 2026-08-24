"""Step 5b: assemble scenes + voice + captions + music into the final 9:16 MP4.

Handles Arabic captions with RTL rendering via libass (ffmpeg subtitles filter).
"""
from __future__ import annotations
from pathlib import Path
import subprocess, random
from .. import config

MUSIC_DIR = config.ASSETS / "music"


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def _concat_scenes(clips: list[Path], out: Path) -> Path:
    """Trim each clip to 9:16 1080x1920 and concat."""
    parts = []
    for i, c in enumerate(clips):
        p = out.parent / f"norm_{i:02d}.mp4"
        _run([
            "ffmpeg", "-y", "-i", str(c),
            "-vf",
            f"scale={config.WIDTH}:{config.HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={config.WIDTH}:{config.HEIGHT},fps={config.FPS}",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-pix_fmt", "yuv420p", "-an", str(p),
        ])
        parts.append(p)
    lst = out.parent / "concat.txt"
    lst.write_text("\n".join(f"file '{p}'" for p in parts))
    _run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0",
        "-i", str(lst), "-c", "copy", str(out),
    ])
    return out


def _build_srt(words: list[dict], chunks: list[str], out: Path) -> Path:
    """Group word timings into caption chunks (2-5 words each)."""
    def fmt(t: float) -> str:
        h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
        return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")

    lines, wi = [], 0
    for idx, chunk in enumerate(chunks, 1):
        need = len(chunk.split())
        window = words[wi: wi + need]
        if not window:
            break
        start = window[0]["start"]
        end = window[-1]["end"]
        lines.append(f"{idx}\n{fmt(start)} --> {fmt(end)}\n{chunk}\n")
        wi += need
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def compose(
    scene_clips: list[Path],
    voice_mp3: Path,
    captions_srt: Path,
    out: Path,
    language: str = "en",
) -> Path:
    tmp_video = out.parent / "video_only.mp4"
    _concat_scenes(scene_clips, tmp_video)

    music_files = list(MUSIC_DIR.glob("*.mp3"))
    music = random.choice(music_files) if music_files else None

    # Pick font by language
    font_path = (
        config.CAPTION_FONT_AR if language == "ar" else config.CAPTION_FONT_EN
    ).as_posix()

    # Bright kid-friendly caption style, purple outline
    style = (
        f"FontName={'Cairo' if language == 'ar' else 'Baloo 2'},"
        "FontSize=20,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&HFF5B7B,BorderStyle=1,Outline=3,Shadow=1,"
        "Alignment=2,MarginV=200"
    )
    vf = (
        f"subtitles='{captions_srt.as_posix()}':force_style='{style}'"
    )

    if music:
        _run([
            "ffmpeg", "-y",
            "-i", str(tmp_video),
            "-i", str(voice_mp3),
            "-i", str(music),
            "-filter_complex",
            f"[0:v]{vf}[v];"
            "[1:a]volume=1.0[a1];"
            "[2:a]volume=0.10,afade=t=in:st=0:d=1,afade=t=out:st=52:d=3[a2];"
            "[a1][a2]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(out),
        ])
    else:
        # No music yet — just voice + captions
        _run([
            "ffmpeg", "-y",
            "-i", str(tmp_video),
            "-i", str(voice_mp3),
            "-filter_complex",
            f"[0:v]{vf}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart",
            str(out),
        ])
    return out
