"""Step 5b: assemble scenes + voice + captions + music into the final 9:16 MP4.

Works for both facts (narration+bgmusic) and songs (sung audio only).
"""
from __future__ import annotations
from pathlib import Path
import subprocess, random
from .. import config

MUSIC_DIR = config.ASSETS / "music"


def _overlays_vf(target: float) -> str:
    """Return ffmpeg overlay filters for retention boosts:
    - Hook flash: bright yellow 'MAGIC INSIDE!' text in first 2s
    - Subscribe CTA: 'SUBSCRIBE for daily magic!' in last 2s
    Both use drawtext with fontcolor + shadow, no external font file needed.
    """
    cta_start = max(0.5, target - 2.5)
    # DejaVu Sans is present in the sandbox/container by default
    font = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    hook = (
        f"drawtext=fontfile={font}:text='MAGIC INSIDE\\!':"
        "fontsize=120:fontcolor=yellow:borderw=6:bordercolor=black:"
        "x=(w-text_w)/2:y=h*0.15:"
        "enable='between(t,0,2)'"
    )
    cta = (
        f"drawtext=fontfile={font}:text='SUBSCRIBE for daily magic\\!':"
        "fontsize=70:fontcolor=white:borderw=5:bordercolor=purple:"
        "x=(w-text_w)/2:y=h*0.82:"
        f"enable='between(t,{cta_start},{target})'"
    )
    return f"{hook},{cta}"


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
    """Fact captions from forced alignment.

    Ignores the plan's caption text (which may paraphrase the narration).
    Instead, chunks the ACTUAL narration words into ~6-word segments, using
    real timings from force_align so captions perfectly match speech.
    """
    if not words:
        out.write_text("", encoding="utf-8")
        return out

    # ElevenLabs alignment returns {text, start, end} where text may be a word,
    # punctuation, or whitespace. Filter to real words and merge.
    def _tok(w):
        return (w.get("text") or w.get("word") or "").strip()

    real = [w for w in words if _tok(w)]
    if not real:
        out.write_text("", encoding="utf-8")
        return out

    # Chunk into caption windows of ~6 words each, breaking on punctuation.
    MAX_WORDS = 7
    BREAK_CHARS = ".!?,"
    windows = []
    cur = []
    for w in real:
        tok = _tok(w)
        # Attach punctuation tokens to previous window without incrementing count
        if tok in BREAK_CHARS + ";:" and cur:
            cur.append(w)
            windows.append(cur)
            cur = []
            continue
        cur.append(w)
        ends_at_punct = tok[-1] in BREAK_CHARS
        real_word_count = sum(1 for x in cur if _tok(x) not in BREAK_CHARS + ";:")
        if real_word_count >= MAX_WORDS or (ends_at_punct and real_word_count >= 3):
            windows.append(cur)
            cur = []
    if cur:
        windows.append(cur)

    lines = []
    for idx, window in enumerate(windows, 1):
        start = window[0]["start"]
        end = window[-1]["end"]
        # Reconstruct text: space between words, no space before punctuation
        parts = []
        for w in window:
            tok = _tok(w)
            if not tok:
                continue
            if tok in BREAK_CHARS + ";:" and parts:
                parts[-1] = parts[-1] + tok
            else:
                parts.append(tok)
        text = " ".join(parts).strip()
        lines.append(f"{idx}\n{_fmt(start)} --> {_fmt(end)}\n{text}\n")

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
    max_duration: float = 55.0,
) -> Path:
    tmp_video = out.parent / "video_only.mp4"
    _concat_scenes(scene_clips, tmp_video)

    def _dur(p: Path) -> float:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, check=True,
        )
        return float(r.stdout.strip())

    voice_dur = _dur(voice_mp3)
    target = min(max_duration, voice_dur)

    music_files = list(MUSIC_DIR.glob("*.mp3"))
    music = random.choice(music_files) if music_files else None
    vf = f"subtitles='{captions_srt.as_posix()}':force_style='{_caption_style()}',{_overlays_vf(target)}"
    fade_start = max(0.0, target - 2.0)

    if music:
        _run([
            "ffmpeg", "-y",
            "-i", str(tmp_video), "-i", str(voice_mp3), "-i", str(music),
            "-filter_complex",
            f"[0:v]{vf},trim=duration={target},setpts=PTS-STARTPTS[v];"
            f"[1:a]atrim=duration={target},asetpts=PTS-STARTPTS,volume=1.0,afade=t=out:st={fade_start}:d=2[a1];"
            f"[2:a]atrim=duration={target},asetpts=PTS-STARTPTS,volume=0.10,afade=t=in:st=0:d=1,afade=t=out:st={fade_start}:d=2[a2];"
            "[a1][a2]amix=inputs=2:duration=first:dropout_transition=0[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out),
        ])
    else:
        _run([
            "ffmpeg", "-y",
            "-i", str(tmp_video), "-i", str(voice_mp3),
            "-filter_complex",
            f"[0:v]{vf},trim=duration={target},setpts=PTS-STARTPTS[v];"
            f"[1:a]atrim=duration={target},asetpts=PTS-STARTPTS,afade=t=out:st={fade_start}:d=2[a]",
            "-map", "[v]", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart", str(out),
        ])
    return out


def compose_song(
    scene_clips: list[Path],
    song_mp3: Path,
    captions_srt: Path,
    out: Path,
    max_duration: float = 55.0,
) -> Path:
    """Sung song: single audio track, karaoke-style captions.

    Loops video clips to cover the audio duration so the song never gets
    cut short by -shortest. Trims final output to max_duration (< 60s Shorts).
    """
    tmp_video = out.parent / "video_only.mp4"
    _concat_scenes(scene_clips, tmp_video)

    # Actual durations
    def _dur(p: Path) -> float:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(p)],
            capture_output=True, text=True, check=True,
        )
        return float(r.stdout.strip())

    audio_dur = _dur(song_mp3)
    video_dur = _dur(tmp_video)
    target = min(max_duration, audio_dur)

    # If video shorter than target, loop it
    if video_dur < target:
        looped = out.parent / "video_looped.mp4"
        loops_needed = int(target / video_dur) + 1
        lst = out.parent / "loop.txt"
        lst.write_text("\n".join(f"file '{tmp_video}'" for _ in range(loops_needed)))
        _run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(lst), "-c", "copy", str(looped),
        ])
        tmp_video = looped

    vf = f"subtitles='{captions_srt.as_posix()}':force_style='{_caption_style()}',{_overlays_vf(target)}"
    # Add fade-out on audio in last 2 seconds so song ends cleanly at cut
    fade_start = max(0.0, target - 2.0)
    _run([
        "ffmpeg", "-y",
        "-i", str(tmp_video), "-i", str(song_mp3),
        "-filter_complex",
        f"[0:v]{vf},trim=duration={target},setpts=PTS-STARTPTS[v];"
        f"[1:a]atrim=duration={target},asetpts=PTS-STARTPTS,afade=t=out:st={fade_start}:d=2[a]",
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(out),
    ])
    return out
