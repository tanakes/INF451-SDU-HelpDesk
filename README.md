# SDU Help Desk Bot — Render Migration

Port of the buda.im SDU Help Desk bot to a self-hosted Telegram webhook on Render, with Render Postgres for persistence and NVIDIA Nemotron 3.5 Lightning as the LLM.

## What was migrated
From your buda.im backup (`sprint5-unfinished-sdu-helpdesk-backup.tar.gz`):
- `knowledge_base/` — official SDU grounding docs (tuition, registration, dormitory, transcripts, campus_services, 32 academic regulations)
- `documents/` — US-04 dispatch manifest + `SDU_map.jpg`
- Behavioral rules from `SOUL.md` (no asterisks, double line breaks, no `#` headings, strict grounding, Kazakh/Russian/English, escalation chain)

## Prerequisites
1. **Telegram Bot Token** — talk to @BotFather, create a bot, copy the token.
2. **Render account** — create a web service + Postgres database.
3. **NVIDIA API key** — https://integrate.api.nvidia.com (Nemotron 3.5 Lightning 30B).

## Local setup
```bash
cd sdu-helpdesk-render
cp .env.example .env
# edit .env with your BOT_TOKEN, NVIDIA_API_KEY, DATABASE_URL, STAFF_GROUP_CHAT_ID
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Deploy to Render
Option A — Manual (recommended, API is limited for DB creation):
- Create a Postgres database in Render dashboard (Starter plan, free) — copy connection string → `DATABASE_URL`
- Create a Web Service → connect GitHub repo `tanakes/INF451-SDU-HelpDesk`
  - Build command: `pip install -r requirements.txt`
  - Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Add env vars: `BOT_TOKEN`, `NVIDIA_API_KEY`, `DATABASE_URL`, `STAFF_GROUP_CHAT_ID` (= `tsk2V5TyqHMpUCevygQ`)
- Optional: `WEBHOOK_SECRET`

Option B — Render Blueprint:
- Push this folder to GitHub
- In Render: "Blueprint" → connect repo → it reads `render.yaml`
- Set `BOT_TOKEN`, `NVIDIA_API_KEY`, `DATABASE_URL`, `WEBHOOK_SECRET`, `STAFF_GROUP_CHAT_ID` as env vars

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
- Or ping `GET /` every 10 minutes (keeps it awake)

## Env vars
| Var | Required | Description |
|---|---|---|
| `BOT_TOKEN` | yes | From @BotFather |
| `NVIDIA_API_KEY` | yes | From https://integrate.api.nvidia.com |
| `DATABASE_URL` | yes | Render Postgres connection string |
| `WEBHOOK_SECRET` | no | Secret token Telegram sends for webhook verification |
| `STAFF_GROUP_CHAT_ID` | no | Authorized staff group chat ID (default from SOUL.md) |
| `PORT` | no | Set by Render automatically |
