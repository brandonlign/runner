from __future__ import annotations

import runpy
from pathlib import Path

from orbittrace_crossyear_core_hdbscan_v1.single_linkage_accessor_compat import (
    install_single_linkage_raw_tree_compat,
)


def main() -> None:
    install_single_linkage_raw_tree_compat()
    frozen_runner = Path(__file__).with_name("run_development.py")
    runpy.run_path(str(frozen_runner), run_name="__main__")


if __name__ == "__main__":
    main()
