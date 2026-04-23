from __future__ import annotations

from pathlib import Path


def find_large_files(files: list[Path], threshold_mb: int) -> list[Path]:
    threshold_bytes = threshold_mb * 1024 * 1024
    return [path for path in files if path.is_file() and path.stat().st_size > threshold_bytes]


def split_large_file(path: Path, chunk_lines: int) -> list[Path]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines(keepends=True)
    if len(lines) <= chunk_lines:
        return []

    chunks: list[Path] = []
    base = path.with_suffix(path.suffix + ".part")
    for idx in range(0, len(lines), chunk_lines):
        target = base.with_name(f"{base.name}{idx // chunk_lines + 1}")
        target.write_text("".join(lines[idx:idx + chunk_lines]), encoding="utf-8")
        chunks.append(target)
    return chunks

