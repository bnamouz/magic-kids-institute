"""Step 5b: assemble scenes + voice + captions + music into the final 9:16 MP4."""
from __future__ import annotations
from pathlib import Path
import json, subprocess, tempfile, random
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
    out.write_text("\n".join(lines))
    return out


def compose(
    scene_clips: list[Path],
    voice_mp3: Path,
    captions_srt: Path,
    out: Path,
) -> Path:
    tmp_video = out.parent / "video_only.mp4"
    _concat_scenes(scene_clips, tmp_video)

    music = random.choice(list(MUSIC_DIR.glob("*.mp3")))
    font_path = config.CAPTION_FONT.as_posix().replace(":", "\\:")

    style = (
        "FontName=Inter,FontSize=18,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H80000000,BorderStyle=1,Outline=2,Shadow=1,"
        "Alignment=2,MarginV=180"
    )
    vf = f"subtitles='{captions_srt.as_posix()}':force_style='{style}'"

    _run([
        "ffmpeg", "-y",
        "-i", str(tmp_video),
        "-i", str(voice_mp3),
        "-i", str(music),
        "-filter_complex",
        f"[0:v]{vf}[v];"
        "[1:a]volume=1.0[a1];"
        "[2:a]volume=0.12,afade=t=in:st=0:d=1,afade=t=out:st=52:d=3[a2];"
        "[a1][a2]amix=inputs=2:duration=first:dropout_transition=0[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart",
        str(out),
    ])
    return out
