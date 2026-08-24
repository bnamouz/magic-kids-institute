"""Step 5b: assemble scenes + voice + captions + music into the final 9:16 MP4.

Works for both facts (narration+bgmusic) and songs (sung audio only).
"""
from __future__ import annotations
from pathlib import Path
import subprocess, random
from .. import config

MUSIC_DIR = config.ASSETS / "music"


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def _concat_scenes(clips: list[Path], out: Path) -> Path:
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


def _fmt(t: float) -> str:
    h = int(t // 3600); m = int((t % 3600) // 60); s = t % 60
    return f"{h:02d}:{m:02d}:{s:06.3f}".replace(".", ",")


def build_srt_from_alignment(words: list[dict], chunks: list[str], out: Path) -> Path:
    """Fact captions from forced alignment."""
    lines, wi = [], 0
    for idx, chunk in enumerate(chunks, 1):
        need = len(chunk.split())
        window = words[wi: wi + need]
        if not window:
            break
        start = window[0]["start"]; end = window[-1]["end"]
        lines.append(f"{idx}\n{_fmt(start)} --> {_fmt(end)}\n{chunk}\n")
        wi += need
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def build_srt_evenly(captions: list[str], audio_dur: float, out: Path) -> Path:
    """Song captions distributed evenly across the sung audio."""
    caps = [c for c in captions if c.strip()]
    per = audio_dur / len(caps)
    lines = []
    for i, c in enumerate(caps):
        lines.append(f"{i+1}\n{_fmt(i*per)} --> {_fmt((i+1)*per)}\n{c}\n")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def _caption_style() -> str:
    return (
        "FontName=Baloo 2,FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&HFF5B7B,BorderStyle=1,Outline=3,Shadow=1,"
        "Alignment=2,MarginV=200"
    )


def compose_fact(
    scene_clips: list[Path],
    voice_mp3: Path,
    captions_srt: Path,
    out: Path,
) -> Path:
    tmp_video = out.parent / "video_only.mp4"
    _concat_scenes(scene_clips, tmp_video)

    music_files = list(MUSIC_DIR.glob("*.mp3"))
    music = random.choice(music_files) if music_files else None
    vf = f"subtitles='{captions_srt.as_posix()}':force_style='{_caption_style()}'"

    if music:
        _run([
            "ffmpeg", "-y",
            "-i", str(tmp_video), "-i", str(voice_mp3), "-i", str(music),
            "-filter_complex",
            f"[0:v]{vf}[v];"
            "[1:a]volume=1.0[a1];"
            "[2:a]volume=0.10,afade=t=in:st=0:d=1,afade=t=out:st=52:d=3[a2];"
            "[a1][a2]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(out),
        ])
    else:
        _run([
            "ffmpeg", "-y",
            "-i", str(tmp_video), "-i", str(voice_mp3),
            "-filter_complex", f"[0:v]{vf}[v]",
            "-map", "[v]", "-map", "1:a",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(out),
        ])
    return out


def compose_song(
    scene_clips: list[Path],
    song_mp3: Path,
    captions_srt: Path,
    out: Path,
) -> Path:
    """Sung song: single audio track, karaoke-style captions."""
    tmp_video = out.parent / "video_only.mp4"
    _concat_scenes(scene_clips, tmp_video)
    vf = f"subtitles='{captions_srt.as_posix()}':force_style='{_caption_style()}'"
    _run([
        "ffmpeg", "-y",
        "-i", str(tmp_video), "-i", str(song_mp3),
        "-filter_complex", f"[0:v]{vf}[v]",
        "-map", "[v]", "-map", "1:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest", "-movflags", "+faststart", str(out),
    ])
    return out
