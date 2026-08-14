#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import math
from typing import Any, Callable

import numpy as np

QUERY_CHUNK = 128


def exact_chunked_atoms(mod: Any, events: list[dict[str, Any]], pair_d: Callable[[dict[str, Any], dict[str, Any]], float]) -> list[Any]:
    """Frozen RFT atoms() with only bounded-memory KD query scheduling changed."""
    by_bin: dict[int, list[dict[str, Any]]] = mod.defaultdict(list)
    for event in events:
        bidx = int(math.floor((event['coord'] - mod.BLIND[1]) / mod.BIN_WIDTH))
        by_bin[bidx].append(event)

    out: list[Any] = []
    for bidx in sorted(by_bin):
        rows = by_bin[bidx]
        if len(rows) < mod.MIN_ATOM:
            continue
        lon = np.asarray([row['lon'] for row in rows], float)
        lat = np.asarray([row['lat'] for row in rows], float)
        vg = np.asarray([row['vg'] for row in rows], float)
        uv = mod.unit(lon, lat)
        transformed = np.column_stack((
            uv / (2.0 * math.sin(math.radians(3.0) / 2.0)),
            np.log(vg) / math.log(1.08),
        ))
        tree = mod.cKDTree(transformed)
        neighbor_sets: list[list[int]] = [[] for _ in rows]

        for start in range(0, len(rows), QUERY_CHUNK):
            end = min(len(rows), start + QUERY_CHUNK)
            candidate_chunk = tree.query_ball_point(transformed[start:end], r=1.02)
            if len(candidate_chunk) != end - start:
                raise RuntimeError(f'chunked KD candidate count changed in bin {bidx}')
            for offset, candidates in enumerate(candidate_chunk):
                i = start + offset
                distances = []
                for raw_j in candidates:
                    j = int(raw_j)
                    if j == i:
                        continue
                    d = pair_d(rows[i], rows[j])
                    if d <= 1.0 + 1e-12:
                        distances.append((d, mod.event_id(rows[j]), j))
                distances.sort(key=lambda item: (item[0], item[1]))
                neighbor_sets[i] = [j for _d, _eid, j in distances[:mod.KNN]]
            del candidate_chunk

        adjacency = [set() for _ in rows]
        for i, neighbors in enumerate(neighbor_sets):
            for j in neighbors:
                if i in neighbor_sets[j]:
                    adjacency[i].add(j)
                    adjacency[j].add(i)

        seen: set[int] = set()
        for seed in range(len(rows)):
            if seed in seen:
                continue
            stack = [seed]
            component: list[int] = []
            seen.add(seed)
            while stack:
                i = stack.pop()
                component.append(i)
                for j in sorted(adjacency[i]):
                    if j not in seen:
                        seen.add(j)
                        stack.append(j)
            if len(component) < mod.MIN_ATOM:
                continue
            medoid_rows = []
            for i in component:
                distances = [pair_d(rows[i], rows[j]) for j in component if j != i]
                medoid_rows.append((float(np.median(distances)) if distances else 0.0, mod.event_id(rows[i]), i))
            medoid_residual, _member_id, _medoid_index = min(medoid_rows)
            center_u = uv[component].sum(axis=0)
            center_u /= np.linalg.norm(center_u)
            logv = float(np.median(np.log(vg[component])))
            members = tuple(sorted(mod.event_id(rows[i]) for i in component))
            aid = hashlib.sha256((f'{bidx}|' + '|'.join(members)).encode()).hexdigest()[:16]
            out.append(mod.Atom(
                aid,
                bidx,
                mod.BLIND[1] + (bidx + 0.5) * mod.BIN_WIDTH,
                members,
                center_u,
                logv,
                medoid_residual,
            ))
    return out
