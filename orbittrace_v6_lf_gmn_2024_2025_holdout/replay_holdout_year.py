from __future__ import annotations

from orbittrace_v6_label_free_all_event_null import run_development as lf
from orbittrace_v6_lf_gmn_2024_2025_holdout import holdout_context as ctx

ctx.activate()

# The generic replay is scientifically unchanged. We intercept only frozen
# runtime construction so every inherited year/month/corpus namespace is the
# preregistered 2024/2025 holdout namespace before geometry parsing or
# scan_year_v6 is called.
_real_load_module = lf.load_module


def _holdout_load_module(path, name):
    v6 = _real_load_module(path, name)
    original_load_base = v6.load_base_runner

    def load_base_runner(base_path):
        old = original_load_base(base_path)
        original_load_support = old.load_support_module

        def load_support_module(parts):
            support = original_load_support(parts)
            ctx.configure_runtime(v6, old, support)
            return support

        old.load_support_module = load_support_module
        return old

    v6.load_base_runner = load_base_runner
    return v6


lf.load_module = _holdout_load_module

from orbittrace_v6_label_free_all_event_null_fanout import replay_exact_year as replay  # noqa: E402


def main() -> int:
    return replay.main()


if __name__ == "__main__":
    raise SystemExit(main())
