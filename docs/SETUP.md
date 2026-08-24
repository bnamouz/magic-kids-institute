# Magic Kids Institute — Setup Guide (step-by-step)

You'll finish with a fully automated YouTube Kids Shorts channel that publishes
one English video in the morning and one Arabic video in the evening — every
day, without touching it.

## Step 1 — Create a dedicated Google account (5 min)

Do NOT use your personal Gmail — you want this channel isolated.

1. Open [accounts.google.com/signup](https://accounts.google.com/signup) in Chrome incognito.
2. Suggested email: `magickidsinstitute@gmail.com`
3. Save the password in your password manager.
4. Stay signed in.

## Step 2 — Create the YouTube channel with the right settings (5 min)

1. Open [youtube.com](https://youtube.com) while signed in as the new Google account.
2. Click your avatar → **Create a channel**.
3. Channel name: `Magic Kids Institute`
4. Handle: `@MagicKidsInstitute` (already verified free)
5. Upload avatar: [`magickids_avatar.png`](../assets/magickids_avatar.png)
6. Upload banner: [`magickids_banner.png`](../assets/magickids_banner.png)
7. In **YouTube Studio → Settings → Channel → Advanced settings**, set:
   - **Audience: "Yes, set this channel as made for kids"**  ← required
   - This disables comments, personalized ads, notifications, and stories on every video

## Step 3 — Enable the YouTube Data API v3 (5 min)

1. Go to [console.cloud.google.com](https://console.cloud.google.com) with the same Google account.
2. Create a new project: `MagicKidsInstitute`
3. In the search bar type "YouTube Data API v3" → **Enable**.
4. Go to **APIs & Services → OAuth consent screen**:
   - User type: **External**
   - App name: `Magic Kids Institute Uploader`
   - Support email: your email
   - Save → Publish app
5. Go to **APIs & Services → Credentials**:
   - **Create Credentials → OAuth client ID → Desktop app**
   - Download the JSON file
   - Rename it to `youtube_client_secret.json`
   - Save it inside the project folder (root, next to `README.md`)

## Step 4 — Gather API keys (10 min)

Get each of these keys and paste them into a new file called `.env` (copy `.env.example`):

| Key | Where to get it | Note |
|---|---|---|
| `OPENAI_API_KEY` | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | ~$0.05/video |
| `FAL_API_KEY` | [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys) | ~$0.40/video |
| `ELEVENLABS_API_KEY` | [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys) | Starter plan $5/mo covers 60+ videos |
| `SUPABASE_URL` | Already set: `https://imtpxkbimtolhvlyynvx.supabase.co` | |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase project → Settings → API → `service_role` (secret) | |

## Step 5 — Test locally (10 min)

```bash
cd magic-kids-institute
pip install -r requirements.txt

# First run — will prompt YouTube OAuth in your browser
RUN_LANGUAGE=en YT_PRIVACY=unlisted python -m src.main
```

This should:
1. Print `[0/6] language: en`
2. Pick a topic like "Why do bees dance?"
3. Write a script, render 6-8 cartoon clips
4. Generate voice, compose the final MP4
5. Open a browser window asking you to authorize YouTube upload — approve it
6. Upload the video as **unlisted**

Watch the unlisted video. If it looks good, run once more with `RUN_LANGUAGE=ar` to test the Arabic pipeline.

## Step 6 — Deploy to Railway with a daily cron (10 min)

1. Go to [railway.app](https://railway.app) → **New Project → Deploy from GitHub**.
2. Pick your `magic-kids-institute` repo.
3. Set all environment variables from your `.env` file in Railway's variables panel.
4. Also add:
   - `YT_PRIVACY=public` (once you're confident)
   - Upload `youtube_client_secret.json` and `youtube_token.json` as files (or paste their contents as env vars — see docs)
5. Add **two cron jobs**:
   - Name: `daily-en` — Schedule: `0 7 * * *` (07:00 UTC) — Command: `RUN_LANGUAGE=en python -m src.main`
   - Name: `daily-ar` — Schedule: `0 15 * * *` (15:00 UTC) — Command: `RUN_LANGUAGE=ar python -m src.main`

That's it — you now have an English Short at 07:00 UTC (peak US morning) and
an Arabic Short at 15:00 UTC (peak Middle East evening) every single day.

## Step 7 — Monitor

- Supabase → Table Editor → `videos` — see every run's status
- YouTube Studio → Content — see published videos
- Railway → Deployments → Logs — see live pipeline output

## Cost summary

- OpenAI: ~$0.05/video × 2/day × 30 = **$3/mo**
- fal.ai: ~$0.40/video × 2/day × 30 = **$24/mo**
- ElevenLabs Starter: **$5/mo**
- Supabase free tier: **$0**
- Railway hobby plan: **$5/mo**

**Total ≈ $37/month for 60 kid-safe YouTube Shorts.**
