from __future__ import annotations

from typing import Any

from google import genai

from app.settings import settings


def gemini_client() -> genai.Client:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return genai.Client(api_key=settings.gemini_api_key)


def extract_text(response: Any) -> str:
    """
    Best-effort extraction for google-genai responses across versions.
    """
    text = getattr(response, "text", None)
    if isinstance(text, str) and text.strip():
        return text

    # Fall back to candidates[0].content.parts[0].text shape
    candidates = getattr(response, "candidates", None)
    if candidates:
        c0 = candidates[0]
        content = getattr(c0, "content", None)
        parts = getattr(content, "parts", None) if content else None
        if parts:
            t = getattr(parts[0], "text", None)
            if isinstance(t, str):
                return t

    return ""

