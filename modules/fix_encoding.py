from __future__ import annotations

import unicodedata


def decode_text(data: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def normalize_encoding_text(text: str) -> tuple[str, list[str]]:
    actions: list[str] = []
    original = text

    normalized = unicodedata.normalize("NFC", text)
    if normalized != text:
        text = normalized
        actions.append("normalized_unicode")

    cleaned = "".join(ch for ch in text if _is_valid_char(ch))
    if cleaned != text:
        text = cleaned
        actions.append("removed_invalid_control_chars")

    return text, actions if text != original else []


def _is_valid_char(ch: str) -> bool:
    code = ord(ch)
    if ch in ("\n", "\r", "\t"):
        return True
    return code >= 32

