from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path


class SmartLogger:
    def __init__(self, log_path: Path, max_size_mb: int = 10) -> None:
        self.log_path = log_path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._rotate_if_needed()

    def log(self, event: str, **data: object) -> None:
        payload = {
            "ts": datetime.now(UTC).isoformat(),
            "event": event,
            **data,
        }
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    def _rotate_if_needed(self) -> None:
        if self.log_path.exists() and self.log_path.stat().st_size > self.max_size_bytes:
            backup = self.log_path.with_suffix(self.log_path.suffix + ".1")
            if backup.exists():
                backup.unlink()
            self.log_path.replace(backup)

