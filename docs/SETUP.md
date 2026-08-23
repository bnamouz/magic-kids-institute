# Setup — CurioDrop AI (≈25 minutes end-to-end)

You'll do this once. After that, one video ships every morning at 07:00 UTC (10:00 שעון ישראל) with zero clicks.

## 1. Create the YouTube channel (3 min)

1. Sign into any Google account (or create a fresh one dedicated to the channel — recommended).
2. Go to **[youtube.com/create_channel](https://www.youtube.com/create_channel)** and create a new channel.
3. Open **YouTube Studio → Customization → Basic Info**, and set the handle to **`@CurioDropAI`**.
   - Fallbacks if you decide otherwise later: `@WonderDropAI`, `@MicroMindDaily`, `@CuriousDropDaily`.
4. Upload a channel logo (a stylized water-drop with a brain silhouette — I've included a Canva template link in `docs/BRAND.md`).
5. Description:
   > CurioDrop is your one-minute mind-drop — a fresh piece of wonder every morning. Follow along for the strangest, sweetest, most delightful facts in the universe.

## 2. Enable the YouTube Data API (5 min)

1. Open **[console.cloud.google.com](https://console.cloud.google.com)** in the SAME Google account that owns the channel.
2. Create a project called `curio-drop`.
3. **APIs & Services → Library →** enable **YouTube Data API v3**.
4. **APIs & Services → OAuth consent screen →** External → fill required fields → add scope `https://www.googleapis.com/auth/youtube.upload` → add your own email as a **test user**.
5. **APIs & Services → Credentials →** Create Credentials → **OAuth client ID** → Desktop app → download JSON as `youtube_client_secret.json` and put it in the project root.
6. Run once locally: `python -m src.main` — a browser will open and finish OAuth, then save `youtube_token.json`. Keep that file safe; Railway will use it too.

## 3. Supabase project (3 min)

1. In your existing Supabase account create a project `curio-drop`.
2. SQL editor → run:

    ```sql
    create table topics (
      id uuid primary key default gen_random_uuid(),
      title text not null,
      angle text,
      used_at timestamptz,
      created_at timestamptz default now()
    );
    create table videos (
      id uuid primary key default gen_random_uuid(),
      topic_id uuid references topics(id),
      youtube_id text,
      title text,
      description text,
      status text,
      error text,
      cost_usd numeric,
      created_at timestamptz default now()
    );
    ```

3. Copy the **Project URL** and **service_role** key into `.env`.

## 4. Third-party API keys (5 min)

| Service        | Where                                                              | Free tier?               |
| -------------- | ------------------------------------------------------------------ | ------------------------ |
| OpenAI         | [platform.openai.com/api-keys](https://platform.openai.com/api-keys) | Pay-as-you-go, $5 covers ~500 videos |
| fal.ai         | [fal.ai/dashboard/keys](https://fal.ai/dashboard/keys)               | $5 free credit           |
| ElevenLabs     | [elevenlabs.io/app/settings/api-keys](https://elevenlabs.io/app/settings/api-keys) | 10k chars/month free |

Paste them into `.env`.

## 5. Seed the topic queue (1 min)

```bash
python -m src.seed_topics
```

Or, better: use the 200-topic list in `prompts/topic_ideas.txt`.

## 6. Dry-run locally (5 min)

```bash
python -m src.main
```

The first run will:

1. open your browser for YouTube OAuth,
2. pop the topic queue,
3. render `output/<today>/final.mp4`,
4. upload it as **Unlisted** (`YT_PRIVACY=unlisted` in `.env`),
5. print the URL. Watch it end-to-end before switching to public.

Once you're happy → set `YT_PRIVACY=public`.

## 7. Deploy to Railway (5 min)

```bash
cd curio-drop-ai
git init && git add -A && git commit -m "curio-drop v1"
railway login
railway init          # new project: curio-drop
railway link
railway up            # deploys Dockerfile
# Add env vars from .env in Railway → Variables
# Upload youtube_client_secret.json and youtube_token.json as base64 secrets
# or better: mount them as Railway secret files.
```

Railway reads `cronSchedule` from `railway.json` and runs the container every day at 07:00 UTC.

## 8. Watch it work

- Every morning, check the `videos` table in Supabase — one new row per day.
- If `status = 'failed'`, the error column tells you exactly which step blew up.
- YouTube Studio → Analytics → Reach → filter by "First 24 hours" tells you which topics hook best; feed winners back into the queue.

That's it — you're live.
