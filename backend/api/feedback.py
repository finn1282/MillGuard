"""One feedback code path, used by POST /api/feedback and by the Telegram buttons."""
from backend import state
from backend.api.models import FeedbackIn


def record(body: FeedbackIn, source: str = "app") -> None:
    state.db().push("feedback", dict(body.model_dump(), source=source), keep=5000)
