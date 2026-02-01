from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class InsightSeverity(str, Enum):
    info = "info"
    warn = "warn"
    highlight = "highlight"


@dataclass(frozen=True)
class Insight:
    """
    A privacy-safe insight object that can be rendered into summary.md later.

    Keep fields general and safe for public output.
    Avoid raw notes, exact timestamps, or any sensitive identifiers.
    """

    key: str
    title: str
    message: str
    severity: InsightSeverity = InsightSeverity.info
    value: Optional[float] = None
    unit: Optional[str] = None
    meta: Optional[dict[str, Any]] = None
