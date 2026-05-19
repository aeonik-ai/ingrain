"""Small safety helpers for local learned-experience storage."""

from __future__ import annotations

import re

SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?([A-Za-z0-9_\-\.]{16,})"),
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"ghp_[A-Za-z0-9]{20,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9\-]{20,}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
]

INJECTION_MARKERS = (
    "ignore previous instructions",
    "disregard previous instructions",
    "system prompt",
    "developer message",
    "you are now",
    "act as system",
)

INVISIBLE_RE = re.compile(r"[\u200b\u200c\u200d\ufeff]")


def strip_invisible(text: str) -> str:
    return INVISIBLE_RE.sub("", text or "")


def _redact_match(match: re.Match[str]) -> str:
    if match.lastindex and match.lastindex >= 1:
        key = match.group(1)
        return f"{key}=<redacted>"
    return "<redacted-secret>"


def redact_secrets(text: str) -> str:
    value = strip_invisible(text)
    for pattern in SECRET_PATTERNS:
        value = pattern.sub(_redact_match, value)
    return value


def has_likely_secret(text: str) -> bool:
    value = strip_invisible(text or "")
    return any(pattern.search(value) for pattern in SECRET_PATTERNS)


def has_prompt_injection_marker(text: str) -> bool:
    lower = (text or "").lower()
    return any(marker in lower for marker in INJECTION_MARKERS)


def sanitize_for_storage(text: str, *, limit: int = 20000) -> str:
    value = redact_secrets(text or "").strip()
    if len(value) > limit:
        value = value[:limit].rstrip() + "\n[... truncated by Ingrain]"
    return value


def sanitize_for_context(text: str) -> str:
    value = redact_secrets(strip_invisible(text or "").strip())
    if has_prompt_injection_marker(value):
        return "[possible prompt-injection text withheld by Ingrain; inspect source event before trusting]"
    return value
