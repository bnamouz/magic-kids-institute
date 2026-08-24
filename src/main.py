"""Magic Kids Institute — daily pipeline entry point.

Runs once per invocation; Railway cron triggers it every 12 h (EN + AR).
Fails loudly so cron marks the run failed. Uses RUN_LANGUAGE env var
to pick the language for this run, or auto-alternates by day-of-year parity.
"""
from __future__ import annotations
import datetime as dt, json, sys, traceback

from . import config, db
from .steps import script, visuals, voice, compose, upload


def _pick_language() -> str:
    """Return 'en' or 'ar' based on RUN_LANGUAGE env var."""
    lang = (config.RUN_LANGUAGE or "auto").lower()
    if lang in ("en", "ar"):
        return lang
    # auto — alternate by day-of-year parity
    doy = dt.date.today().timetuple().tm_yday
    return "en" if doy % 2 == 0 else "ar"


def run() -> None:
    language = _pick_language()
    today = dt.date.today().isoformat()
    run_dir = config.OUTPUT / f"{today}_{language}"
    run_dir.mkdir(parents=True, exist_ok=True)
    video_id = None

    try:
        print(f"[0/6] language: {language}")

        # 1 — topic
        topic = db.next_topic()
        print(f"[1/6] topic: {topic['title']}")

        # 2+3 — script + scenes (in the requested language)
        plan = script.write_script(topic, language=language)
        (run_dir / "plan.json").write_text(
            json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"[2/6] script: {plan['title']}")

        # log a draft row
        video_id = db.log_video(
            topic_id=topic["id"],
            title=plan["title"],
            description=plan["narration"][:500],
            status="draft",
            language=language,
            made_for_kids=True,
        )

        # 4 — visuals
        clips = visuals.render_scenes(plan["scenes"], run_dir / "scenes")
        print(f"[3/6] {len(clips)} clips rendered")

        # 5a — voice + timings
        mp3 = voice.narrate(plan["narration"], run_dir / "voice.mp3", language=language)
        words = voice.force_align(mp3, plan["narration"])
        print(f"[4/6] voiceover + {len(words)} word timings")

        # 5b — captions + compose
        srt = compose._build_srt(words, plan["captions"], run_dir / "captions.srt")
        final = compose.compose(clips, mp3, srt, run_dir / "final.mp4", language=language)
        db.update_video(video_id, status="rendered")
        print(f"[5/6] composed: {final}")

        # 6 — upload
        yt_id = upload.upload_short(
            final, plan["title"], plan["narration"], plan["hashtags"], language=language
        )
        db.update_video(video_id, status="uploaded", youtube_id=yt_id)
        db.mark_topic_used(topic["id"])
        print(f"[6/6] uploaded: https://youtube.com/shorts/{yt_id}")

    except Exception as e:
        traceback.print_exc()
        if video_id:
            db.update_video(video_id, status="failed", error=str(e)[:1000])
        sys.exit(1)


if __name__ == "__main__":
    run()
