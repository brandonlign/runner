from __future__ import annotations

from pathlib import Path
from typing import Any

import run_static_matching as base


_original_load_events = base.load_events


def load_clone_ready_events(path: Path) -> list[dict[str, Any]]:
    events = _original_load_events(path)
    filtered = [event for event in events if event.get("uncertainty_ok", False)]
    if not filtered:
        raise RuntimeError("No clone-ready events remain after the frozen uncertainty screen")
    return filtered


base.load_events = load_clone_ready_events


if __name__ == "__main__":
    base.main()
