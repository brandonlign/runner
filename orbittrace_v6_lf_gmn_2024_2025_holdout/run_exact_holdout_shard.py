from __future__ import annotations

from orbittrace_v6_lf_gmn_2024_2025_holdout import holdout_context as ctx

# Patch only the frozen year/month namespace before the generic exact-shard
# parser resolves its allowed year choices. Exact rescoring itself is
# deterministic and consumes the already-frozen proposal/window payload.
ctx.activate()

from orbittrace_v6_label_free_all_event_null_fanout import run_exact_center_shard as exact  # noqa: E402


def main() -> int:
    return exact.main()


if __name__ == "__main__":
    raise SystemExit(main())
