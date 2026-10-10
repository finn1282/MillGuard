"""Vercel entry. The request path never trains or explains; build-time imports (shap) are stubbed so the bundle stays under 250 MB."""
import sys
import types

try:
    import shap  # noqa: F401
except ImportError:
    sys.modules["shap"] = types.ModuleType("shap")

from backend.api.main import app  # noqa: E402,F401
