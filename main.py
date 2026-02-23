"""
WriteFlow AI - SaaS AI Writing Assistant
Production-ready FastAPI backend
"""

import os
import time
import hashlib
import secrets
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from openai import OpenAI, APIError, RateLimitError

load_dotenv()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MASTER_API_KEY = os.getenv("MASTER_API_KEY", "wf_live_master_key_change_me")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "2048"))

# In production, replace with a database.  For MVP we keep a set in memory.
VALID_ACCESS_TOKENS: set[str] = {
    MASTER_API_KEY,
    # Add more tokens here or manage via admin endpoint
}

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="WriteFlow AI",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Rate limiting (simple in-memory, per-token)
# ---------------------------------------------------------------------------
_rate_limit: dict[str, list[float]] = {}
RATE_LIMIT_WINDOW = 60  # seconds
RATE_LIMIT_MAX = 20     # requests per window


def _check_rate_limit(token: str) -> None:
    now = time.time()
    hits = _rate_limit.setdefault(token, [])
    # Prune old entries
    hits[:] = [t for t in hits if now - t < RATE_LIMIT_WINDOW]
    if len(hits) >= RATE_LIMIT_MAX:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Please wait before making more requests.",
        )
    hits.append(now)


# ---------------------------------------------------------------------------
# Auth dependency
# ---------------------------------------------------------------------------
def _authorize(authorization: Optional[str] = Header(None)) -> str:
    """Validate Bearer token and return the token string."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization format. Use: Bearer <token>")
    token = parts[1]
    if token not in VALID_ACCESS_TOKENS:
        raise HTTPException(status_code=403, detail="Invalid access token")
    _check_rate_limit(token)
    return token


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class GenerateRequest(BaseModel):
    type: str = Field(..., pattern="^(blog|product|email|social)$")
    prompt: str = Field(..., min_length=2, max_length=4000)
    tone: Optional[str] = Field("professional", max_length=50)
    language: Optional[str] = Field("en", max_length=10)


class RewriteRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=8000)
    style: Optional[str] = Field("improved", max_length=50)


class TranslateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=8000)
    source_lang: Optional[str] = Field("auto")
    target_lang: Optional[str] = Field("en")


class AIResponse(BaseModel):
    content: str
    usage: dict
    model: str


# ---------------------------------------------------------------------------
# System prompts per content type
# ---------------------------------------------------------------------------
SYSTEM_PROMPTS = {
    "blog": (
        "You are an expert blog writer and SEO specialist. "
        "Write engaging, well-structured blog content with proper headings (using Markdown), "
        "subheadings, bullet points, and a compelling introduction and conclusion. "
        "Optimize for readability and SEO. Include a meta description suggestion at the end."
    ),
    "product": (
        "You are a world-class copywriter specializing in product descriptions. "
        "Write compelling, benefit-driven product descriptions that convert. "
        "Use power words, highlight key features and benefits, include a call-to-action. "
        "Format with Markdown for readability."
    ),
    "email": (
        "You are an email marketing expert with high conversion rates. "
        "Write professional, engaging emails with a clear subject line suggestion, "
        "compelling body, and strong call-to-action. "
        "Format with Markdown. Include subject line at the top."
    ),
    "social": (
        "You are a social media content strategist. "
        "Create engaging social media posts optimized for engagement. "
        "Include relevant hashtag suggestions, emoji usage where appropriate, "
        "and format for maximum impact. Provide variations for different platforms "
        "(Twitter/X, LinkedIn, Instagram) in Markdown format."
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _call_openai(system: str, user: str) -> AIResponse:
    """Call OpenAI and return structured response."""
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=MAX_TOKENS,
            temperature=0.7,
        )
        return AIResponse(
            content=resp.choices[0].message.content or "",
            usage={
                "prompt_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "completion_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_tokens": resp.usage.total_tokens if resp.usage else 0,
            },
            model=resp.model or MODEL,
        )
    except RateLimitError:
        raise HTTPException(status_code=429, detail="OpenAI rate limit reached. Please try again shortly.")
    except APIError as e:
        raise HTTPException(status_code=502, detail=f"OpenAI API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@app.post("/api/generate", response_model=AIResponse)
async def generate_content(
    body: GenerateRequest,
    authorization: Optional[str] = Header(None),
):
    """Generate content based on type and prompt."""
    _authorize(authorization)

    system = SYSTEM_PROMPTS[body.type]
    if body.tone and body.tone != "professional":
        system += f"\n\nUse a {body.tone} tone throughout."
    if body.language and body.language != "en":
        system += f"\n\nWrite the content in {body.language}."

    return _call_openai(system, body.prompt)


@app.post("/api/rewrite", response_model=AIResponse)
async def rewrite_content(
    body: RewriteRequest,
    authorization: Optional[str] = Header(None),
):
    """Rewrite / improve existing text."""
    _authorize(authorization)

    style_instructions = {
        "improved": "Improve the clarity, flow, and impact while keeping the original meaning.",
        "formal": "Rewrite in a formal, professional tone.",
        "casual": "Rewrite in a casual, conversational tone.",
        "concise": "Make it significantly more concise while keeping key points.",
        "expanded": "Expand with more detail, examples, and depth.",
    }
    instruction = style_instructions.get(body.style or "improved", style_instructions["improved"])

    system = (
        "You are an expert editor and writing coach. "
        f"{instruction} "
        "Return the rewritten text in Markdown format. "
        "After the rewrite, add a brief '---\\n**Changes made:**' section listing key improvements."
    )

    return _call_openai(system, f"Please rewrite the following text:\n\n{body.text}")


@app.post("/api/translate", response_model=AIResponse)
async def translate_content(
    body: TranslateRequest,
    authorization: Optional[str] = Header(None),
):
    """Translate text between languages (defaults to Chinese-English auto-detect)."""
    _authorize(authorization)

    system = (
        "You are a professional translator fluent in all major languages. "
        "Provide accurate, natural-sounding translations that preserve the original tone and meaning. "
        "If the source language is Chinese, translate to English. "
        "If the source language is English, translate to Chinese. "
        "For other language pairs, follow the user's instructions. "
        "Format the output in Markdown. After the translation, add a brief note about any "
        "cultural or contextual adaptations you made."
    )

    user_msg = body.text
    if body.source_lang != "auto":
        user_msg = f"Translate from {body.source_lang} to {body.target_lang}:\n\n{body.text}"

    return _call_openai(system, user_msg)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# ---------------------------------------------------------------------------
# Serve frontend
# ---------------------------------------------------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
