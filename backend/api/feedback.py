"""One feedback code path, used by POST /api/feedback and by the Telegram buttons."""
from pathlib import Path

from backend.api.models import FeedbackIn

ART = Path(__file__).resolve().parents[1] / "artifacts"


def record(body: FeedbackIn, source: str = "app") -> None:
    with open(ART / "feedback.jsonl", "a") as f:
        f.write(body.model_dump_json() + "\n")
