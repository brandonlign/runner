"""Transport-only stub exposing the exact frozen v19 fusion helper."""
from __future__ import annotations


def require(ok: bool, message: str) -> None:
    if not ok:
        raise RuntimeError(message)


def fusion_orders(quality_order: list[str], consensus_order: list[str]) -> dict[str, list[str]]:
    require(set(quality_order) == set(consensus_order), 'fusion universes differ')
    q = {fid: i + 1 for i, fid in enumerate(quality_order)}
    c = {fid: i + 1 for i, fid in enumerate(consensus_order)}
    rank_sum = sorted(quality_order, key=lambda fid: (q[fid] + c[fid], q[fid], c[fid], fid))
    rank_product = sorted(quality_order, key=lambda fid: (q[fid] * c[fid], q[fid] + c[fid], q[fid], c[fid], fid))
    return {
        'consensus_only': list(consensus_order),
        'rank_sum': rank_sum,
        'rank_product': rank_product,
        'v17_control': list(quality_order),
    }
