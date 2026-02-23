# WriteFlow AI

AI-powered writing assistant SaaS. Generate blog posts, product descriptions, emails, social media content. Rewrite and translate text instantly.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/XxxxGith/writeflow-ai)

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/new/template?template=https://github.com/XxxxGith/writeflow-ai)

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

## Deploy to Render (Free)

1. Click the **Deploy to Render** button above
2. Set `OPENAI_API_KEY` and `MASTER_API_KEY` environment variables
3. Done! Your app will be live at `https://writeflow-ai.onrender.com`

## Deploy to Railway

1. Click the **Deploy on Railway** button above
2. Set `OPENAI_API_KEY` and `MASTER_API_KEY` environment variables
3. Deploy - auto-detects `Procfile`

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
