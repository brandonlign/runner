#!/usr/bin/env python3
from __future__ import annotations

from typing import Any


def atoms_without_dead_medoid(mod: Any, events: list[dict[str, Any]]) -> list[Any]:
    """Exact frozen atom construction except for the unused medoid-residual field.

    Frozen RFT v1 never reads Atom.medoid_residual after construction. All fields
    that can affect transitions, tube membership, persistence, trimming, scores,
    IDs, or output ordering are computed with the identical frozen expressions.
    """
    by_bin: dict[int, list[dict[str, Any]]] = mod.defaultdict(list)
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
                d = mod.pair_d(rows[i], rows[j])
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


def assert_probe_equivalence(mod: Any, events: list[dict[str, Any]], probe_size: int = 1500) -> None:
    """Compare every downstream-relevant Atom field on a small deterministic probe."""
    probe = events[: min(probe_size, len(events))]
    frozen = mod.atoms(probe)
    fast = atoms_without_dead_medoid(mod, probe)
    if len(frozen) != len(fast):
        raise RuntimeError("dead-medoid probe changed atom count")
    for a, b in zip(frozen, fast):
        if (a.aid, a.bin_index, a.center, a.members, a.logv) != (b.aid, b.bin_index, b.center, b.members, b.logv):
            raise RuntimeError("dead-medoid probe changed downstream atom fields")
        if not mod.np.array_equal(a.u, b.u):
            raise RuntimeError("dead-medoid probe changed atom direction")
