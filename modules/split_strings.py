from __future__ import annotations

import re
from dataclasses import dataclass


_SIMPLE_STRING_RE = re.compile(r'(?P<prefix>.*?)(?P<quote>["\'])(?P<content>[^"\'\\]{1,})(?P=quote)(?P<suffix>.*)')


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

    match = _SIMPLE_STRING_RE.fullmatch(base)
    if not match:
        return line

    content = match.group("content")
    if len(content) <= max_length:
        return line

    quote = match.group("quote")
    prefix = match.group("prefix")
    suffix = match.group("suffix")
    chunks = [content[i:i + chunk_size] for i in range(0, len(content), chunk_size)]
    rebuilt = " + ".join(f"{quote}{chunk}{quote}" for chunk in chunks)
    return f"{prefix}{rebuilt}{suffix}{newline}"

