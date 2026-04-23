from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SplitResult:
    text: str
    changed: bool
    split_count: int


def split_long_strings(text: str, max_length: int, chunk_size: int) -> SplitResult:
    lines = text.splitlines(keepends=True)
    changed = False
    split_count = 0
    output: list[str] = []

    for line in lines:
        converted = _split_line_if_needed(line, max_length=max_length, chunk_size=chunk_size)
        if converted != line:
            changed = True
            split_count += 1
        output.append(converted)

    return SplitResult("".join(output), changed, split_count)


def _split_line_if_needed(line: str, max_length: int, chunk_size: int) -> str:
    newline = ""
    base = line
    if line.endswith("\n"):
        newline = "\n"
        base = line[:-1]

    parsed = _parse_string_literal(base)
    if not parsed:
        return line

    prefix, quote, content, suffix = parsed
    if len(content) <= max_length:
        return line

    chunks = _chunk_preserving_escapes(content, chunk_size)
    rebuilt = " + ".join(f"{quote}{chunk}{quote}" for chunk in chunks)
    return f"{prefix}{rebuilt}{suffix}{newline}"


def _parse_string_literal(line: str) -> tuple[str, str, str, str] | None:
    start = -1
    quote = ""
    for idx, ch in enumerate(line):
        if ch in ('"', "'"):
            start = idx
            quote = ch
            break
    if start < 0:
        return None

    escaped = False
    end = -1
    for idx in range(start + 1, len(line)):
        ch = line[idx]
        if escaped:
            escaped = False
            continue
        if ch == "\\":
            escaped = True
            continue
        if ch == quote:
            end = idx
            break
    if end < 0:
        return None

    prefix = line[:start]
    content = line[start + 1:end]
    suffix = line[end + 1:]
    return prefix, quote, content, suffix


def _chunk_preserving_escapes(content: str, chunk_size: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []

    for ch in content:
        current.append(ch)
        if len(current) < chunk_size:
            continue
        if _ends_with_unclosed_escape(current):
            continue
        chunks.append("".join(current))
        current = []

    if current:
        chunks.append("".join(current))

    return chunks


def _ends_with_unclosed_escape(chars: list[str]) -> bool:
    slash_count = 0
    for ch in reversed(chars):
        if ch != "\\":
            break
        slash_count += 1
    return slash_count % 2 == 1
