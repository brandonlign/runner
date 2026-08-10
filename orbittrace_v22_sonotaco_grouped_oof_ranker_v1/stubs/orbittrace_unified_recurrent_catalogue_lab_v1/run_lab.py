"""Transport-only stub exposing the exact frozen #839 deterministic fold rule."""
from __future__ import annotations

import hashlib


def deterministic_fold(group: str, folds: int = 5) -> int:
    return int(hashlib.sha256(group.encode("utf-8")).hexdigest()[:8], 16) % folds
