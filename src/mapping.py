from __future__ import annotations
import re
from typing import Tuple, Optional
from rapidfuzz import fuzz

# Heuristics to convert a YouTube title into (artist, track)

REMOVE_PATTERNS = [
    r"\(Official.*?\)",
    r"\[Official.*?\]",
    r"\(Lyrics?\)",
    r"\[Lyrics?\]",
    r"\(Audio\)",
    r"\[Audio\]",
    r"\(Visualizer\)",
    r"\[Visualizer\]",
    r"\(Live.*?\)",
    r"\[Live.*?\]",
    r"\(HD\)",
    r"\[HD\]",
]

SEP_PATTERNS = [" - ", " – ", " — ", " | ", ": "]


def clean_title(title: str) -> str:
    t = title
    for pat in REMOVE_PATTERNS:
        t = re.sub(pat, "", t, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", t).strip()


def guess_artist_title(title: str, channel: Optional[str]) -> Tuple[str, str]:
    t = clean_title(title)
    for sep in SEP_PATTERNS:
        if sep in t:
            left, right = t.split(sep, 1)
            return left.strip(), right.strip()
    # Fallback: if channel looks like artist name, prefer channel as artist
    if channel and fuzz.partial_ratio(channel.lower(), t.lower()) > 60:
        return channel.strip(), t.strip()
    # Otherwise, split on first common separator
    parts = re.split(r"[-–—:\|]", t, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), parts[1].strip()
    return "", t  # unknown artist
