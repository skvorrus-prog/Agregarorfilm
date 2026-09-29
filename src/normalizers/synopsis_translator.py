"""Helper to fetch or translate movie synopses into Russian."""
import logging
import urllib.parse
from typing import Optional
import requests

logger = logging.getLogger(__name__)


def is_mostly_russian(text: str) -> bool:
    """Checks if text contains significant Cyrillic characters."""
    if not text:
        return False
    cyrillic_chars = sum(1 for c in text if '\u0400' <= c <= '\u04FF')
    return cyrillic_chars > 15 or (len(text) > 0 and cyrillic_chars / len(text) > 0.3)


def get_russian_synopsis_from_wikipedia(title: str) -> Optional[str]:
    """Attempts to find a Russian summary from Russian Wikipedia."""
    if not title or len(title.strip()) < 2:
        return None
    try:
        clean_title = title.split("/")[0].strip().replace(" ", "_")
        url = f"https://ru.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(clean_title)}"
        resp = requests.get(url, timeout=4.0, headers={"User-Agent": "DigitalReleasesBot/1.0"})
        if resp.status_code == 200:
            extract = resp.json().get("extract")
            if extract and is_mostly_russian(extract) and len(extract) > 40:
                # If extract contains disambiguation, skip
                if "может означать" in extract or "значения в Википедии" in extract:
                    return None
                return extract
    except Exception:
        pass
    return None


def translate_synopsis_to_russian(english_text: str) -> Optional[str]:
    """Translates English overview to Russian via MyMemory free translation API."""
    if not english_text or is_mostly_russian(english_text):
        return english_text

    # Take first 450 characters to stay within clean query limits
    chunk = english_text[:450].strip()
    if len(chunk) < 10:
        return None

    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(chunk)}&langpair=en|ru"
        resp = requests.get(url, timeout=5.0, headers={"User-Agent": "DigitalReleasesBot/1.0"})
        if resp.status_code == 200:
            data = resp.json()
            translated = data.get("responseData", {}).get("translatedText")
            if translated and is_mostly_russian(translated):
                return translated
    except Exception as e:
        logger.debug(f"Translation error: {e}")

    return english_text


def ensure_russian_synopsis(overview: Optional[str], russian_title: Optional[str] = None) -> Optional[str]:
    """Ensures movie overview is in Russian if possible."""
    if not overview and not russian_title:
        return None

    # If already in Russian, keep it
    if overview and is_mostly_russian(overview):
        return overview

    # Try Wikipedia for Russian title first
    if russian_title:
        wiki_summary = get_russian_synopsis_from_wikipedia(russian_title)
        if wiki_summary:
            return wiki_summary

    # Fallback: translate English overview
    if overview:
        translated = translate_synopsis_to_russian(overview)
        if translated:
            return translated

    return overview
