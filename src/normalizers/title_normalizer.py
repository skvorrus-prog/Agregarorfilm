"""Title normalization and string similarity utilities."""
import re
from difflib import SequenceMatcher
from typing import Optional


ROMAN_NUMERALS = {
    r"\bvii\b": "7",
    r"\bvi\b": "6",
    r"\biv\b": "4",
    r"\bv\b": "5",
    r"\biii\b": "3",
    r"\bii\b": "2",
    r"\bi\b": "1",
    r"\bpart\s+one\b": "part 1",
    r"\bpart\s+two\b": "part 2",
    r"\bpart\s+three\b": "part 3",
}


def normalize_title(title: str) -> str:
    """Normalizes title for robust fuzzy matching."""
    if not title:
        return ""

    s = title.lower()
    # Replace & with and
    s = re.sub(r"&", " and ", s)

    # Replace roman numerals
    for roman, digit in ROMAN_NUMERALS.items():
        s = re.sub(roman, digit, s)

    # Remove all non-alphanumeric unicode characters except space
    s = re.sub(r"[^\w\s]", " ", s)

    # Collapse multiple whitespaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def title_similarity(t1: str, t2: str) -> float:
    """Computes similarity ratio between two titles."""
    n1 = normalize_title(t1)
    n2 = normalize_title(t2)
    if not n1 or not n2:
        return 0.0
    if n1 == n2:
        return 1.0
    return SequenceMatcher(None, n1, n2).ratio()


def extract_year(text: str) -> Optional[int]:
    """Finds a 4-digit year between 1900 and 2099."""
    m = re.search(r"\b(19\d{2}|20\d{2})\b", text)
    if m:
        return int(m.group(1))
    return None
