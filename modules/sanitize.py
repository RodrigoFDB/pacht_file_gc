from __future__ import annotations

import re
from dataclasses import dataclass


_ZERO_WIDTH_RE = re.compile("[\u200B\u200C\u200D\u2060\uFEFF]")


@dataclass
class SanitizeResult:
    text: str
    changed: bool
    actions: list[str]


def sanitize_text(text: str, config: dict) -> SanitizeResult:
    original = text
    actions: list[str] = []

    if config.get("remove_invisible_characters", True):
        updated = _ZERO_WIDTH_RE.sub("", text)
        if updated != text:
            text = updated
            actions.append("removed_invisible_characters")

    if config.get("convert_tabs_to_spaces", True):
        tab_size = int(config.get("tab_size", 4))
        updated = text.replace("\t", " " * tab_size)
        if updated != text:
            text = updated
            actions.append("tabs_to_spaces")

    updated = _normalize_line_endings(text, config.get("line_ending", "LF"))
    if updated != text:
        text = updated
        actions.append("normalized_line_endings")

    if config.get("trim_trailing_spaces", True):
        updated = "\n".join(line.rstrip(" \t") for line in text.splitlines())
        if text.endswith("\n"):
            updated += "\n"
        if updated != text:
            text = updated
            actions.append("trimmed_trailing_spaces")

    return SanitizeResult(text=text, changed=text != original, actions=actions)


def _normalize_line_endings(text: str, line_ending: str) -> str:
    unix = text.replace("\r\n", "\n").replace("\r", "\n")
    if line_ending.upper() == "CRLF":
        return unix.replace("\n", "\r\n")
    return unix
