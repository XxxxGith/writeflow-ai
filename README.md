# WriteFlow AI

AI-powered writing assistant SaaS. Generate blog posts, product descriptions, emails, social media content. Rewrite and translate text instantly.

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

Open `http://localhost:8000` in your browser. Enter your access token in the header bar.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key | required |
| `MASTER_API_KEY` | Admin access token | `wf_live_master_key_change_me` |
| `OPENAI_MODEL` | Model to use | `gpt-4o-mini` |
| `MAX_TOKENS` | Max response tokens | `2048` |
| `PORT` | Server port | `8000` |

## Deploy to Railway

1. Push to GitHub
2. Connect repo on [railway.app](https://railway.app)
3. Set env vars in Railway dashboard
4. Deploy - auto-detects `Procfile`

## Deploy to Render

1. Push to GitHub
2. New Web Service on [render.com](https://render.com)
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set env vars

## API Endpoints

All endpoints require `Authorization: Bearer <token>` header.

- `POST /api/generate` - Generate content (blog/product/email/social)
- `POST /api/rewrite` - Rewrite text
- `POST /api/translate` - Translate text
- `GET /api/health` - Health check
- `GET /docs` - Interactive API docs (Swagger)

## Pricing Model

- Free tier: 5 generations/day
- Pro ($9.99/mo): 200 generations/day
- Business ($29.99/mo): Unlimited + API access
