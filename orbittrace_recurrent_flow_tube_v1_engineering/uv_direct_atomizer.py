#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from typing import Any


def pair_from_existing_uv(mod: Any, ua: Any, ub: Any, vga: float, vgb: float) -> float:
    """Frozen pair_d formula using unit vectors already computed by frozen atoms()."""
    theta = mod.angle_deg(ua, ub) / 3.0
    speed = abs(mod.math.log(vga / vgb)) / mod.math.log(1.08)
    return float(mod.math.hypot(theta, speed))


def assert_uv_pair_equivalence(mod: Any, events: list[dict[str, Any]], sample_count: int = 2048) -> None:
    """Fail closed unless UV-direct distances are bit-identical to frozen pair_d."""
    if len(events) < 2:
        return
    lon = mod.np.asarray([e["lon"] for e in events], float)
    lat = mod.np.asarray([e["lat"] for e in events], float)
    uv = mod.unit(lon, lat)
    n = len(events)
    count = min(sample_count, n - 1)
    for k in range(count):
        i = (k * 7919) % n
        j = (i + 1 + (k * 104729) % (n - 1)) % n
        if j == i:
            j = (j + 1) % n
        frozen = mod.pair_d(events[i], events[j])
        direct = pair_from_existing_uv(mod, uv[i], uv[j], events[i]["vg"], events[j]["vg"])
        if frozen != direct:
            raise RuntimeError(f"UV-direct pair mismatch at sample {k}: {frozen!r} != {direct!r}")


def atoms_uv_direct(mod: Any, events: list[dict[str, Any]]) -> list[Any]:
    """Frozen atom construction with dead medoid removed and pair_d fed existing UVs.

    Neighbor candidate generation, exact distance formula, reciprocal-KNN graph,
    component traversal, atom directions, speeds, IDs, members, centers, and order
    are otherwise identical to frozen RFT v1.
    """
    by_bin: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for e in events:
        idx = int(mod.math.floor((e["coord"] - mod.BLIND[1]) / mod.BIN_WIDTH))
        by_bin[idx].append(e)

    out: list[Any] = []
    for bidx in sorted(by_bin):
        rows = by_bin[bidx]
        if len(rows) < mod.MIN_ATOM:
            continue
        lon = mod.np.asarray([r["lon"] for r in rows], float)
        lat = mod.np.asarray([r["lat"] for r in rows], float)
        vg = mod.np.asarray([r["vg"] for r in rows], float)
        uv = mod.unit(lon, lat)
        transformed = mod.np.column_stack((
            uv / (2.0 * mod.math.sin(mod.math.radians(3.0) / 2.0)),
            mod.np.log(vg) / mod.math.log(1.08),
        ))
        tree = mod.cKDTree(transformed)

        neighbor_sets: list[list[int]] = []
        for i in range(len(rows)):
            candidates = tree.query_ball_point(transformed[i], r=1.02)
            ds = []
            for j in candidates:
                if j == i:
                    continue
                d = pair_from_existing_uv(mod, uv[i], uv[j], rows[i]["vg"], rows[j]["vg"])
                if d <= 1.0 + 1e-12:
                    ds.append((d, mod.event_id(rows[j]), j))
            ds.sort(key=lambda x: (x[0], x[1]))
            neighbor_sets.append([j for _d, _eid, j in ds[:mod.KNN]])

        adj = [set() for _ in rows]
        for i, ns in enumerate(neighbor_sets):
            for j in ns:
                if i in neighbor_sets[j]:
                    adj[i].add(j)
                    adj[j].add(i)

        seen = set()
        for seed in range(len(rows)):
            if seed in seen:
                continue
            stack = [seed]
            comp = []
            seen.add(seed)
            while stack:
                i = stack.pop()
                comp.append(i)
                for j in sorted(adj[i]):
                    if j not in seen:
                        seen.add(j)
                        stack.append(j)
            if len(comp) < mod.MIN_ATOM:
                continue

            uu = uv[comp].sum(axis=0)
            uu /= mod.np.linalg.norm(uu)
            logv = float(mod.np.median(mod.np.log(vg[comp])))
            members = tuple(sorted(mod.event_id(rows[i]) for i in comp))
            aid = mod.hashlib.sha256((f"{bidx}|" + "|".join(members)).encode()).hexdigest()[:16]
            out.append(mod.Atom(
                aid,
                bidx,
                mod.BLIND[1] + (bidx + 0.5) * mod.BIN_WIDTH,
                members,
                uu,
                logv,
                0.0,
            ))
    return out


def _signature(a: Any) -> tuple[Any, ...]:
    return (a.aid, a.bin_index, a.center, a.members, a.logv, a.u.tobytes())


def assert_atom_probe_equivalence(mod: Any, events: list[dict[str, Any]], dead: Any, sample_size: int = 6000) -> None:
    """Fail closed unless UV-direct atoms match exact dead-medoid atoms."""
    if len(events) <= sample_size:
        probe = list(events)
    else:
        step = max(1, len(events) // sample_size)
        probe = list(events[::step][:sample_size])
    assert_uv_pair_equivalence(mod, probe, sample_count=min(2048, max(0, len(probe) - 1)))
    reference = dead.atoms_without_dead_medoid(mod, probe)
    candidate = atoms_uv_direct(mod, probe)
    if len(reference) != len(candidate):
        raise RuntimeError("UV-direct probe changed atom count")
    for i, (a, b) in enumerate(zip(reference, candidate)):
        if _signature(a) != _signature(b):
            raise RuntimeError(f"UV-direct probe changed atom {i}")
