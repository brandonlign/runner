from __future__ import annotations

import hashlib
from pathlib import Path

SOURCE = Path(__file__).with_name("analyze_track1.py")

BOOTSTRAP_OLD = "bootstrap_medians = np.median(nop_radiant[bootstrap_indices], axis=1)"
BOOTSTRAP_NEW = "bootstrap_medians = np.median(np.asarray(nop_radiant, dtype=float)[bootstrap_indices], axis=1)"

ORBIT_OLD = '''def orbit_distance_matrix(a: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = a if b is None else np.asarray(b, dtype=float)
    e1, q1 = a[:, 0][:, None], a[:, 1][:, None]
    e2, q2 = b[:, 0][None, :], b[:, 1][None, :]
    i1, n1 = np.deg2rad(a[:, 2])[:, None], np.deg2rad(a[:, 4])[:, None]
    i2, n2 = np.deg2rad(b[:, 2])[None, :], np.deg2rad(b[:, 4])[None, :]
    plane = np.arccos(np.clip(
        np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(n1 - n2), -1, 1
    ))
    p1, p2 = perihelion_vector(a), perihelion_vector(b)
    peri = np.arccos(np.clip(p1 @ p2.T, -1, 1))
    d2 = (
        (e1 - e2) ** 2 + (q1 - q2) ** 2 + (2 * np.sin(plane / 2)) ** 2
        + (((e1 + e2) / 2) * 2 * np.sin(peri / 2)) ** 2
    )
    return np.sqrt(np.maximum(d2, 0.0))
'''

ORBIT_NEW = '''def orbit_distance_matrix(a: np.ndarray, b: np.ndarray | None = None) -> np.ndarray:
    a = np.asarray(a, dtype=float)
    b = a if b is None else np.asarray(b, dtype=float)
    e1, q1 = a[:, 0][:, None], a[:, 1][:, None]
    e2, q2 = b[:, 0][None, :], b[:, 1][None, :]
    i1 = np.deg2rad(a[:, 2])[:, None]
    w1 = np.deg2rad(a[:, 3])[:, None]
    o1 = np.deg2rad(a[:, 4])[:, None]
    i2 = np.deg2rad(b[:, 2])[None, :]
    w2 = np.deg2rad(b[:, 3])[None, :]
    o2 = np.deg2rad(b[:, 4])[None, :]
    delta_node = np.arctan2(np.sin(o1 - o2), np.cos(o1 - o2))
    plane = np.arccos(np.clip(
        np.cos(i1) * np.cos(i2) + np.sin(i1) * np.sin(i2) * np.cos(delta_node), -1, 1
    ))
    peri_argument = (
        np.cos((i1 + i2) / 2) * np.sin(delta_node / 2)
        / np.maximum(np.cos(plane / 2), 1e-12)
    )
    peri_difference = w1 - w2 + 2 * np.arcsin(np.clip(peri_argument, -1, 1))
    d2 = (
        (e1 - e2) ** 2 + (q1 - q2) ** 2 + (2 * np.sin(plane / 2)) ** 2
        + (((e1 + e2) / 2) * 2 * np.sin(peri_difference / 2)) ** 2
    )
    return np.sqrt(np.maximum(d2, 0.0))
'''


def exact_replace(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected exactly one {label} expression, found {count}")
    return text.replace(old, new)


def main() -> None:
    raw = SOURCE.read_bytes()
    text = raw.decode("utf-8")
    repaired = exact_replace(text, BOOTSTRAP_OLD, BOOTSTRAP_NEW, "bootstrap indexing")
    repaired = exact_replace(repaired, ORBIT_OLD, ORBIT_NEW, "orbit-distance implementation")
    print("source_sha256", hashlib.sha256(raw).hexdigest())
    print("repaired_sha256", hashlib.sha256(repaired.encode("utf-8")).hexdigest())
    namespace = {
        "__name__": "__main__",
        "__file__": str(SOURCE.with_name("analyze_track1_runtime.py")),
    }
    exec(compile(repaired, namespace["__file__"], "exec"), namespace)


if __name__ == "__main__":
    main()
