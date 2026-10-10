"""The one place for the LLM provider: an OpenAI-compatible endpoint (Grafilab by default). Swap provider via backend/.env only.
The key is read from the environment and never printed or logged."""
import logging
import os

from backend.notify.store import load_env

logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)


def settings():
    load_env()
    return dict(key=os.environ.get("LLM_API_KEY", ""), base=os.environ.get("LLM_BASE_URL") or "https://llm.grafilab.ai/v1",
                model=os.environ.get("LLM_MODEL") or "gemini/gemini-3-flash")


def configured() -> bool:
    return bool(settings()["key"])


def model() -> str:
    return settings()["model"]


def complete(system: str, user: str) -> str:
    from openai import OpenAI
    s = settings()
    client = OpenAI(api_key=s["key"], base_url=s["base"], timeout=30, max_retries=0)
    r = client.chat.completions.create(model=s["model"], temperature=0.3,
                                       messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    return r.choices[0].message.content or ""
