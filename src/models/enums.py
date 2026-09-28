"""Domain enumerations for releases, resolutions, statuses and pipelines."""
from enum import Enum


class ReleaseStatus(str, Enum):
    ANNOUNCED = "ANNOUNCED"
    DIGITAL_RELEASE = "DIGITAL_RELEASE"
    WEB_RELEASE = "WEB_RELEASE"
    BLURAY_RELEASE = "BLURAY_RELEASE"
    UHD_RELEASE = "UHD_RELEASE"
    UPDATED = "UPDATED"


class QualityType(str, Enum):
    WEB_DL = "WEB-DL"
    WEB_RIP = "WEBRip"
    BLURAY = "BluRay"
    REMUX = "REMUX"
    UHD_BLURAY = "UHD BluRay"
    UNKNOWN = "unknown"


class Resolution(str, Enum):
    RES_480P = "480p"
    RES_720P = "720p"
    RES_1080P = "1080p"
    RES_2160P = "2160p"
    UNKNOWN = "unknown"


class PipelineStatus(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


class EventType(str, Enum):
    DIGITAL_PREMIERE = "DIGITAL_PREMIERE"
    WEB_DL_DETECTED = "WEB_DL_DETECTED"
    BLURAY_DETECTED = "BLURAY_DETECTED"
    RU_AUDIO_DETECTED = "RU_AUDIO_DETECTED"
    UHD_DETECTED = "UHD_DETECTED"
    RELEASE_DETECTED = "RELEASE_DETECTED"
