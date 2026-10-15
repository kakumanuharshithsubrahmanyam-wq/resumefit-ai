import re
from typing import List, Tuple

SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+|\n+")
WORD_BOUNDARY = re.compile(r"[a-z0-9+#./\-\s]{2,}", re.IGNORECASE)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_sentences(text: str) -> List[str]:
    parts = SENTENCE_SPLIT.split(text.strip())
    return [normalize_text(part) for part in parts if normalize_text(part)]


def snippet_around(haystack: str, needle: str, radius: int = 90) -> str:
    lower_hay = haystack.lower()
    lower_needle = needle.lower()
    index = lower_hay.find(lower_needle)
    if index < 0:
        return normalize_text(haystack[: min(len(haystack), radius * 2)])
    start = max(0, index - radius)
    end = min(len(haystack), index + len(needle) + radius)
    excerpt = haystack[start:end].strip()
    if start > 0:
        excerpt = f"…{excerpt}"
    if end < len(haystack):
        excerpt = f"{excerpt}…"
    return excerpt


def find_skill_mentions(text: str, variants: List[str]) -> List[Tuple[str, str]]:
    """Return list of (variant, evidence snippet) in order of appearance."""
    lower = text.lower()
    found: List[Tuple[str, str]] = []
    seen = set()
    for variant in sorted(variants, key=len, reverse=True):
        pattern = re.compile(rf"(?<![a-z0-9]){re.escape(variant.lower())}(?![a-z0-9])")
        match = pattern.search(lower)
        if match and variant.lower() not in seen:
            seen.add(variant.lower())
            found.append((variant, snippet_around(text, variant)))
    return found
