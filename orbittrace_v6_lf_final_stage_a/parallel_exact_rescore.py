from __future__ import annotations

import multiprocessing as mp
import os
from typing import Any, Callable

_ORIGINAL: Callable[..., list[dict[str, Any]]] | None = None
_CONTEXT: tuple[Any, list[dict[str, Any]], dict[str, dict[str, Any]], Any, Any] | None = None


def _run_chunk(chunk: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if _ORIGINAL is None or _CONTEXT is None:
        raise RuntimeError("parallel exact-rescore worker context not initialized")
    old, window_events, event_lookup, support, base = _CONTEXT
    return _ORIGINAL(old, chunk, window_events, event_lookup, support, base)


def _split_contiguous(records: list[dict[str, Any]], count: int) -> list[list[dict[str, Any]]]:
    count = max(1, min(int(count), len(records)))
    q, r = divmod(len(records), count)
    chunks: list[list[dict[str, Any]]] = []
    start = 0
    for index in range(count):
        stop = start + q + (1 if index < r else 0)
        chunks.append(records[start:stop])
        start = stop
    if start != len(records) or any(not chunk for chunk in chunks):
        raise RuntimeError("invalid contiguous exact-rescore partition")
    if [row for chunk in chunks for row in chunk] != records:
        raise RuntimeError("exact-rescore partition changed record order")
    return chunks


def install(v6: Any, *, workers: int = 4, min_parallel_records: int = 256) -> dict[str, Any]:
    original = v6.exact_rescore_window_v6
    if getattr(original, "_orbittrace_parallel_exact_wrapper", False):
        raise RuntimeError("parallel exact-rescore wrapper already installed")
    cpu_count = max(1, int(os.cpu_count() or 1))
    worker_count = min(max(1, int(workers)), cpu_count, 4)
    threshold = max(1, int(min_parallel_records))

    def replacement(old, records, window_events, event_lookup, support, base):
        if len(records) < threshold or worker_count <= 1:
            return original(old, records, window_events, event_lookup, support, base)
        if "fork" not in mp.get_all_start_methods():
            raise RuntimeError("exact-equivalent parallel executor requires multiprocessing fork")
        chunks = _split_contiguous(records, min(worker_count, len(records)))
        global _ORIGINAL, _CONTEXT
        _ORIGINAL = original
        _CONTEXT = (old, window_events, event_lookup, support, base)
        try:
            ctx = mp.get_context("fork")
            with ctx.Pool(processes=len(chunks)) as pool:
                chunk_results = pool.map(_run_chunk, chunks, chunksize=1)
        finally:
            _CONTEXT = None
            _ORIGINAL = None
        merged = [row for chunk in chunk_results for row in chunk]
        if len(merged) != len(records):
            raise RuntimeError("parallel exact-rescore changed output cardinality")
        if [str(row["proposal_anchor_id"]) for row in merged] != [str(row["proposal_anchor_id"]) for row in records]:
            raise RuntimeError("parallel exact-rescore changed proposal order")
        print(f"V6_LF_FINAL_PARALLEL_EXACT workers={len(chunks)} proposals={len(records):,}", flush=True)
        return merged

    replacement._orbittrace_parallel_exact_wrapper = True
    replacement._orbittrace_original = original
    v6.exact_rescore_window_v6 = replacement
    return {"workers": worker_count, "min_parallel_records": threshold, "start_method": "fork"}
