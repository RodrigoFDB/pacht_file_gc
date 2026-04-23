from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter, deque
from pathlib import Path

from modules.fix_encoding import decode_text, normalize_encoding_text
from modules.logs import SmartLogger
from modules.optimize import find_large_files, split_large_file
from modules.sanitize import sanitize_text
from modules.split_strings import split_long_strings


TEXT_EXTENSIONS = {
    ".cs",
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".json",
    ".xml",
    ".yml",
    ".yaml",
    ".md",
    ".txt",
    ".config",
    ".props",
    ".targets",
}

STRING_SPLIT_EXTENSIONS = {
    ".py",
    ".cs",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".go",
    ".rs",
    ".cpp",
    ".c",
    ".h",
    ".hpp",
}


class LoopDetector:
    def __init__(self, state_file: Path, window: int, threshold: int) -> None:
        self.state_file = state_file
        self.window = max(window, 1)
        self.threshold = max(threshold, 2)
        self.history = deque(self._load_state(), maxlen=self.window)

    def observe(self, path: Path) -> bool:
        token = str(path)
        self.history.append(token)
        self._save_state()
        return Counter(self.history)[token] >= self.threshold

    def _load_state(self) -> list[str]:
        if not self.state_file.exists():
            return []
        try:
            payload = json.loads(self.state_file.read_text(encoding="utf-8"))
            entries = payload.get("history", [])
            if isinstance(entries, list):
                return [str(entry) for entry in entries][-self.window:]
        except (json.JSONDecodeError, OSError):
            return []
        return []

    def _save_state(self) -> None:
        self.state_file.write_text(json.dumps({"history": list(self.history)}), encoding="utf-8")


def load_config(config_path: Path) -> dict:
    return json.loads(config_path.read_text(encoding="utf-8"))


def iter_candidate_files(root: Path, ignored_dirs: set[str]) -> list[Path]:
    paths: list[Path] = []
    for path in root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in ignored_dirs for part in path.parts):
            continue
        if path.suffix.lower() in TEXT_EXTENSIONS:
            paths.append(path)
    return paths


def is_generated_file(path: Path, patterns: list[str]) -> bool:
    lowered = path.name.lower()
    return any(lowered.endswith(pattern.lower()) for pattern in patterns)


def sanitize_generated_text(text: str) -> tuple[str, list[str]]:
    original = text
    lines = text.splitlines()
    normalized: list[str] = []
    blank_count = 0
    for line in lines:
        is_blank = not line.strip()
        if is_blank:
            blank_count += 1
            if blank_count > 1:
                continue
        else:
            blank_count = 0
        normalized.append(line.rstrip())
    updated = "\n".join(normalized) + ("\n" if text.endswith("\n") else "")
    actions = ["generated_file_reformatted"] if updated != original else []
    return updated, actions


def cleanup_temporary(root: Path, config: dict, logger: SmartLogger) -> int:
    removed = 0
    for directory in config.get("cleanup_directories", []):
        target = root / directory
        if target.exists() and target.is_dir():
            shutil.rmtree(target)
            removed += 1
            logger.log("cleanup_directory", path=str(target))

    cleanup_extensions = tuple(config.get("cleanup_extensions", []))
    for path in root.rglob("*"):
        if path.is_file() and path.suffix.lower() in cleanup_extensions:
            path.unlink()
            removed += 1
            logger.log("cleanup_file", path=str(path))
    return removed


def run(root: Path, config_path: Path) -> dict:
    config = load_config(config_path)
    logger = SmartLogger(
        log_path=root / ".patch_fix_gc" / "patch_fix_gc.log",
        max_size_mb=int(config.get("max_log_file_mb", 10)),
    )
    loop_detector = LoopDetector(
        state_file=root / ".patch_fix_gc" / "state.json",
        window=int(config.get("detect_get_file_loop_window", 30)),
        threshold=int(config.get("detect_get_file_loop_threshold", 10)),
    )

    files = iter_candidate_files(root, set(config.get("ignored_directories", [])))
    large_files = find_large_files(files, int(config.get("large_file_threshold_mb", 2)))
    for path in large_files:
        logger.log("large_file_detected", path=str(path), size=path.stat().st_size)

    changed_count = 0
    split_events = 0
    loops_detected = 0

    for path in files:
        data = path.read_bytes()
        text = decode_text(data)
        actions: list[str] = []

        text, encoding_actions = normalize_encoding_text(text)
        actions.extend(encoding_actions)

        sanitize_result = sanitize_text(text, config)
        text = sanitize_result.text
        actions.extend(sanitize_result.actions)

        if path.suffix.lower() in STRING_SPLIT_EXTENSIONS:
            split_result = split_long_strings(
                text,
                max_length=int(config.get("max_string_length", 400)),
                chunk_size=int(config.get("string_chunk_size", 120)),
            )
            text = split_result.text
            if split_result.changed:
                split_events += split_result.split_count
                actions.append("split_long_strings")
                logger.log("long_string_detected", path=str(path), count=split_result.split_count)

        if is_generated_file(path, config.get("generated_file_patterns", [])):
            text, generated_actions = sanitize_generated_text(text)
            actions.extend(generated_actions)

        encoded = text.encode("utf-8")
        if encoded != data:
            path.write_bytes(encoded)
            changed_count += 1
            logger.log("file_fixed", path=str(path), actions=actions)

        if loop_detector.observe(path):
            loops_detected += 1
            logger.log("get_file_loop_detected", path=str(path), suggestion="clean Copilot cache")

    if config.get("enable_optional_split_large_files", False):
        for path in large_files:
            parts = split_large_file(path, int(config.get("large_file_chunk_lines", 2000)))
            if parts:
                logger.log("large_file_split", path=str(path), parts=[str(part) for part in parts])

    removed = cleanup_temporary(root, config, logger)
    summary = {
        "files_scanned": len(files),
        "files_changed": changed_count,
        "long_string_events": split_events,
        "loops_detected": loops_detected,
        "cleanup_items_removed": removed,
        "large_files_detected": len(large_files),
        "log_file": str(root / ".patch_fix_gc" / "patch_fix_gc.log"),
    }
    logger.log("summary", **summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="patch_fix_gc - universal stability filter for Copilot in VS2022")
    parser.add_argument("--root", default=".", help="Project root directory")
    parser.add_argument("--config", default="config.json", help="Path to config.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).resolve()
    config_path = Path(args.config).resolve()
    if not config_path.exists():
        config_path = root / "config.json"
    summary = run(root=root, config_path=config_path)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
