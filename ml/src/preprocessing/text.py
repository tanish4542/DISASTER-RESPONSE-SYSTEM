"""Conservative, reusable text normalization for disaster messages."""

from __future__ import annotations

import re
from typing import Any

_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
_MENTION_RE = re.compile(r"(?<!\w)@\w+")
_HASHTAG_RE = re.compile(r"(?<!\w)#([A-Za-z0-9_]+)")
_WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(value: Any) -> str:
    """Normalize message artifacts without removing useful semantic content."""
    if value is None:
        return ""
    try:
        if value != value:  # NaN and pandas.NA compare unequal to themselves.
            return ""
    except (TypeError, ValueError):
        pass
    if type(value).__module__.startswith("pandas") and str(value) in {"<NA>", "NaT"}:
        return ""

    text = str(value)
    text = _URL_RE.sub(" URL ", text)
    text = _MENTION_RE.sub(" USER ", text)
    text = _HASHTAG_RE.sub(r" \1 ", text)
    text = text.replace("\n", " ").replace("\r", " ")
    text = _WHITESPACE_RE.sub(" ", text).strip().lower()
    return text
