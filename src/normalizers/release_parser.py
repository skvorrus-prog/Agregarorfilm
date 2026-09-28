"""Release string parser extracting quality, resolution, HDR, audio, and language."""
import re
from typing import Optional, Tuple
from pydantic import BaseModel

from src.models.enums import QualityType, Resolution


class ParsedRelease(BaseModel):
    title: str
    original_title: Optional[str] = None
    year: Optional[int] = None
    quality: str = QualityType.UNKNOWN.value
    resolution: str = Resolution.UNKNOWN.value
    hdr: Optional[str] = None
    audio: Optional[str] = None
    language: Optional[str] = None
    release_group: Optional[str] = None
    raw_title: str


class ReleaseParser:
    """Parses standard scene / P2P release names and multi-lingual release titles."""

    @staticmethod
    def parse_title_and_year(raw: str) -> Tuple[str, Optional[str], Optional[int]]:
        """
        Parses title, original title (if dual language), and year.
        Example: 'Что мы скрываем / What We Hide (2025) WEB-DLRip'
                 -> ('Что мы скрываем', 'What We Hide', 2025)
        Example: 'Oppenheimer.2023.2160p.WEB-DL.DDP5.1.Atmos'
                 -> ('Oppenheimer', None, 2023)
        """
        clean = raw.strip()

        # Check for dual language pattern: 'Title RU / Original Title (Year) ...'
        dual_match = re.match(r"^([^/]+)\s*/\s*([^(|]+?)\s*\((\d{4})\)", clean)
        if dual_match:
            ru_title = dual_match.group(1).strip()
            orig_title = dual_match.group(2).strip()
            year = int(dual_match.group(3))
            return ru_title, orig_title, year

        # Check for single title with (Year)
        single_year_match = re.match(r"^([^(|/]+?)\s*\((\d{4})\)", clean)
        if single_year_match:
            title = single_year_match.group(1).strip()
            year = int(single_year_match.group(2))
            return title, None, year

        # Dot-separated scene release: 'Movie.Title.2024.1080p...'
        dot_year_match = re.search(r"\b(19\d{2}|20\d{2})\b", clean)
        if dot_year_match:
            year = int(dot_year_match.group(1))
            prefix = clean[:dot_year_match.start()].replace(".", " ").replace("_", " ").strip()
            if prefix:
                return prefix, None, year

        # If no year found, clean dot separators
        cleaned = re.sub(r"[\._]", " ", clean)
        cleaned = re.sub(r"\b(2160p|1080p|720p|480p|web-?dl|webrip|bluray|remux).*", "", cleaned, flags=re.IGNORECASE)
        return cleaned.strip() or raw, None, None

    @classmethod
    def parse_quality(cls, text: str) -> str:
        t = text.lower()
        if re.search(r"\b(uhd[- .]?bluray|2160p[- .]?bluray)\b", t):
            return QualityType.UHD_BLURAY.value
        if re.search(r"\bremux\b", t):
            return QualityType.REMUX.value
        if re.search(r"\b(bluray|bdrip|brrip)\b", t):
            return QualityType.BLURAY.value
        if re.search(r"\b(web[- .]?dl|webdl|web-?dlrip)\b", t):
            return QualityType.WEB_DL.value
        if re.search(r"\b(web[- .]?rip|webrip)\b", t):
            return QualityType.WEB_RIP.value
        return QualityType.UNKNOWN.value

    @classmethod
    def parse_resolution(cls, text: str) -> str:
        t = text.lower()
        if re.search(r"\b(2160p|4k|uhd)\b", t):
            return Resolution.RES_2160P.value
        if re.search(r"\b1080[pi]?\b", t):
            return Resolution.RES_1080P.value
        if re.search(r"\b720p\b", t):
            return Resolution.RES_720P.value
        if re.search(r"\b(480p|576p)\b", t):
            return Resolution.RES_480P.value
        return Resolution.UNKNOWN.value

    @classmethod
    def parse_hdr(cls, text: str) -> Optional[str]:
        t = text.upper()
        has_dv = bool(re.search(r"\b(DOLBY[- .]?VISION|DV|DOVI)\b", t))
        has_hdr10_plus = bool(re.search(r"\bHDR10\+", t) or "HDR10PLUS" in t)
        has_hdr10 = bool(re.search(r"\bHDR10\b", t))
        has_hdr = bool(re.search(r"\bHDR\b", t))

        if has_dv and (has_hdr10 or has_hdr):
            return "Dolby Vision / HDR10"
        if has_dv:
            return "Dolby Vision"
        if has_hdr10_plus:
            return "HDR10+"
        if has_hdr10:
            return "HDR10"
        if has_hdr:
            return "HDR"
        return None

    @classmethod
    def parse_audio(cls, text: str) -> Optional[str]:
        t = text.upper()
        parts = []
        if "ATMOS" in t:
            parts.append("Atmos")
        elif "TRUEHD" in t:
            parts.append("TrueHD")
        elif re.search(r"\bDTS[- .]?HD\b", t):
            parts.append("DTS-HD")
        elif re.search(r"\b(DDP|DD\+|EAC3)\b", t):
            parts.append("DDP")

        channels_match = re.search(r"(?:^|\D)(7\.1|5\.1|2\.0)(?:\D|$)", t)
        if channels_match:
            parts.append(channels_match.group(1))

        return " ".join(parts) if parts else None

    @classmethod
    def parse_language(cls, text: str) -> Optional[str]:
        t = text.upper()
        # Russian audio signals
        if re.search(r"\b(RUS|RUSSIAN|РУССКИЙ|ДУБЛЯЖ|DUB|MVO|LVO|AVO|D|P2|L)\b", t):
            return "RU"
        if re.search(r"\b(ENG|ENGLISH)\b", t):
            return "EN"
        if re.search(r"\b(MULTI|DUAL)\b", t):
            return "MULTI"
        return None

    @classmethod
    def parse_release_group(cls, text: str) -> Optional[str]:
        # Scene group after trailing hyphen: ...-GROUP
        m = re.search(r"-([A-Za-z0-9]{2,15})(?:\s*\[.*\])?$", text.strip())
        if m:
            grp = m.group(1)
            # Avoid matching codecs or resolutions as groups
            if grp.upper() not in ("X264", "X265", "HEVC", "AVC", "1080P", "720P", "2160P"):
                return grp
        # Alternative format: | Group
        pipe_m = re.search(r"\|\s*([A-Za-z0-9\s]{2,20})$", text.strip())
        if pipe_m:
            return pipe_m.group(1).strip()
        return None

    @classmethod
    def parse(cls, raw_title: str) -> ParsedRelease:
        """Fully parses a raw release string."""
        title, orig_title, year = cls.parse_title_and_year(raw_title)
        quality = cls.parse_quality(raw_title)
        resolution = cls.parse_resolution(raw_title)
        hdr = cls.parse_hdr(raw_title)
        audio = cls.parse_audio(raw_title)
        language = cls.parse_language(raw_title)
        group = cls.parse_release_group(raw_title)

        return ParsedRelease(
            title=title,
            original_title=orig_title,
            year=year,
            quality=quality,
            resolution=resolution,
            hdr=hdr,
            audio=audio,
            language=language,
            release_group=group,
            raw_title=raw_title,
        )
