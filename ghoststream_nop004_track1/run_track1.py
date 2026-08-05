from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE = Path(__file__).with_name("analyze_track1.py")
OLD = "bootstrap_medians = np.median(nop_radiant[bootstrap_indices], axis=1)"
NEW = "bootstrap_medians = np.median(np.asarray(nop_radiant, dtype=float)[bootstrap_indices], axis=1)"


def main() -> None:
    raw = SOURCE.read_bytes()
    text = raw.decode("utf-8")
    if text.count(OLD) != 1:
        raise RuntimeError(f"Expected exactly one bootstrap indexing expression, found {text.count(OLD)}")
    repaired = text.replace(OLD, NEW)
    print("source_sha256", hashlib.sha256(raw).hexdigest())
    print("repaired_sha256", hashlib.sha256(repaired.encode("utf-8")).hexdigest())
    namespace = {
        "__name__": "__main__",
        "__file__": str(SOURCE.with_name("analyze_track1_runtime.py")),
    }
    exec(compile(repaired, namespace["__file__"], "exec"), namespace)


if __name__ == "__main__":
    main()
