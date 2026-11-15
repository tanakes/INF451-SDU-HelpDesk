# SDU Help Desk Bot — Render Migration

Port of the buda.im SDU Help Desk bot to a self-hosted Telegram webhook on Render, with Neon Postgres for persistence and Gemini (free tier) as the LLM.

## What was migrated
From your buda.im backup (`sprint5-unfinished-sdu-helpdesk-backup.tar.gz`):
- `knowledge_base/` — official SDU grounding docs (tuition, registration, dormitory, transcripts, campus_services, 32 academic regulations)
- `documents/` — US-04 dispatch manifest + `SDU_map.jpg`
- Behavioral rules from `SOUL.md` (no asterisks, double line breaks, no `#` headings, strict grounding, Kazakh/Russian/English, escalation chain)

## Prerequisites
1. **Telegram Bot Token** — talk to @BotFather, create a bot, copy the token.
2. **Render account** — create a web service + Postgres database.
3. **Neon** (optional) — or use Render's built-in Postgres via `render.yaml`.
4. **Gemini API key** — https://aistudio.google.com (free tier).

## Local setup
```bash
cd sdu-helpdesk-render
cp .env.example .env
# edit .env with your BOT_TOKEN, GEMINI_API_KEY, DATABASE_URL, STAFF_GROUP_CHAT_ID
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Deploy to Render
Option A — Render Blueprint (recommended):
- Push this folder to GitHub
- In Render: "Blueprint" → connect repo → it reads `render.yaml`
- Adds a web service + Postgres DB automatically
- Set `BOT_TOKEN`, `GEMINI_API_KEY`, `WEBHOOK_SECRET`, `STAFF_GROUP_CHAT_ID` as env vars (not synced from repo)

Option B — Manual:
- Create a Python web service, connect a Postgres DB
- Build: `pip install -r requirements.txt`
- Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Set the same env vars

## Set the Telegram webhook
Once deployed at `https://your-app.onrender.com`, set the webhook:
```bash
curl -X POST "https://api.telegram.org/bot<BOT_TOKEN>/setWebhook" \
     -d url="https://your-app.onrender.com/webhook/<BOT_TOKEN>"
```
Optional secret token:
```
.../setWebhook?url=...&secret_token=<WEBHOOK_SECRET>
```

## Free-tier caveat (Render)
Render's free web service spins down after ~15 min inactivity. The first Telegram message after a spin-down may be delayed ~20–40 s (cold start). Options:
- Pay $7/mo for a "Starter" web service (no spin-down)
- Or ping `GET /` every 10 minutes (keeps it awake, but first hit still has a small cold start)

## Env vars
| Var | Required | Description |
|---|---|---|
| `BOT_TOKEN` | yes | From @BotFather |
| `GEMINI_API_KEY` | yes | From Google AI Studio |
| `DATABASE_URL` | yes | Neon or Render Postgres connection string |
| `WEBHOOK_SECRET` | no | Secret token Telegram sends for webhook verification |
| `STAFF_GROUP_CHAT_ID` | no | Authorized staff group chat ID (default from SOUL.md) |
| `PORT` | no | Set by Render automatically |
