"""Magic Kids Institute — daily pipeline entry point.

Env: CONTENT_TYPE = 'fact' | 'song'.
Railway runs this twice a day: 07:00 UTC fact, 15:00 UTC song.
"""
from __future__ import annotations
import datetime as dt, json, sys, traceback
from pathlib import Path

from . import config, db
from .steps import script, visuals, voice, compose, upload, song as song_step, thumbnail


LUMI_PREFIX = (
    "Lumi the mascot (cheerful glowing yellow lightbulb with big smiley eyes, "
    "tiny rounded arms, rosy cheeks, purple base, sparkles around her) is prominent "
    "in this scene. "
)


def run_fact(run_dir: Path) -> None:
    topic = db.next_topic("fact")
    print(f"[1/6] fact topic: {topic['title']}")

    plan = script.write_script(topic)
    (run_dir / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[2/6] script: {plan['title']}")

    video_id = db.log_video(
        topic_id=topic["id"], title=plan["title"],
        description=plan["narration"][:500], status="draft",
        content_type="fact", made_for_kids=True,
    )

    try:
        clips = visuals.render_scenes(plan["scenes"], run_dir / "scenes")
        print(f"[3/6] {len(clips)} clips rendered")

        mp3 = voice.narrate(plan["narration"], run_dir / "voice.mp3")
        words = voice.force_align(mp3, plan["narration"])
        print(f"[4/6] voice + {len(words)} timings")

        srt = compose.build_srt_from_alignment(words, plan["captions"], run_dir / "captions.srt")
        final = compose.compose_fact(clips, mp3, srt, run_dir / "final.mp4")
        db.update_video(video_id, status="rendered")
        print(f"[5/6] composed: {final}")

        thumb = None
        try:
            thumb = thumbnail.make_thumbnail({"title": plan["title"]}, run_dir / "thumb.jpg")
            print(f"[5b/6] thumbnail: {thumb}")
        except Exception as te:
            print(f"[5b/6] thumbnail generation failed (non-fatal): {te}")

        yt_id = upload.upload_short(final, plan["title"], plan["narration"], plan["hashtags"], thumbnail_path=thumb)
        db.update_video(video_id, status="uploaded", youtube_id=yt_id)
        db.mark_topic_used(topic["id"])
        print(f"[6/6] uploaded: https://youtube.com/shorts/{yt_id}")
    except Exception as e:
        db.update_video(video_id, status="failed", error=str(e)[:1000])
        raise


def run_song(run_dir: Path) -> None:
    topic = db.next_topic("song")
    print(f"[1/6] song topic: {topic['title']}")

    plan = song_step.write_song(topic)
    (run_dir / "plan.json").write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[2/6] lyrics: {plan['title']}")

    # Inject Lumi mascot into every image prompt
    for s in plan["scenes"]:
        s["image_prompt"] = LUMI_PREFIX + s["image_prompt"]

    video_id = db.log_video(
        topic_id=topic["id"], title=plan["title"],
        description=plan["lyrics"][:500], status="draft",
        content_type="song", made_for_kids=True,
    )

    try:
        clips = visuals.render_scenes(plan["scenes"], run_dir / "scenes")
        print(f"[3/6] {len(clips)} clips rendered")

        song_mp3 = song_step.compose_song(
            plan["lyrics"], plan["music_prompt"], run_dir / "song.mp3", target_seconds=40,
        )
        print(f"[4/6] song audio: {song_mp3.stat().st_size // 1024} KB")

        # Get audio duration
        import subprocess
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(song_mp3)],
            capture_output=True, text=True, check=True,
        )
        dur = float(r.stdout.strip())

        # Force-align sung audio to lyrics so captions match the singing
        aligned_words = []
        try:
            # Strip section tags like [Verse 1], [Chorus] for alignment
            import re as _re
            spoken = _re.sub(r"\[[^\]]+\]", "", plan["lyrics"]).strip()
            aligned_words = voice.force_align(song_mp3, spoken)
            print(f"[4b/6] song alignment: {len(aligned_words)} timings")
        except Exception as ae:
            print(f"[4b/6] song alignment failed (fallback to even): {ae}")

        srt = compose.build_srt_song_synced(
            aligned_words, plan["captions"], dur, run_dir / "captions.srt"
        )
        final = compose.compose_song(clips, song_mp3, srt, run_dir / "final.mp4")
        db.update_video(video_id, status="rendered")
        print(f"[5/6] composed: {final}")

        thumb = None
        try:
            thumb = thumbnail.make_thumbnail({"title": plan["title"]}, run_dir / "thumb.jpg")
            print(f"[5b/6] thumbnail: {thumb}")
        except Exception as te:
            print(f"[5b/6] thumbnail generation failed (non-fatal): {te}")

        yt_id = upload.upload_short(final, plan["title"], plan["lyrics"], plan["hashtags"], thumbnail_path=thumb)
        db.update_video(video_id, status="uploaded", youtube_id=yt_id)
        db.mark_topic_used(topic["id"])
        print(f"[6/6] uploaded: https://youtube.com/shorts/{yt_id}")
    except Exception as e:
        db.update_video(video_id, status="failed", error=str(e)[:1000])
        raise


def run() -> None:
    ctype = config.CONTENT_TYPE.lower()
    today = dt.date.today().isoformat()
    run_dir = config.OUTPUT / f"{today}_{ctype}"
    run_dir.mkdir(parents=True, exist_ok=True)
    print(f"[0/6] content_type: {ctype}")
    try:
        if ctype == "fact":
            run_fact(run_dir)
        elif ctype == "song":
            run_song(run_dir)
        else:
            raise ValueError(f"CONTENT_TYPE must be 'fact' or 'song', got {ctype!r}")
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    run()
