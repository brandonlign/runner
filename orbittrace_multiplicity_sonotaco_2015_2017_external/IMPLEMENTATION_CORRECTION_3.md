# Implementation-only correction 3 — duplicated parser hash literals inside frozen runner

Status: recorded before any SonotaCo 2015 or 2017 archive access.

Retry2 passed every workflow-level pre-data guard, then invoked the frozen scientific runner. The runner stopped at its own duplicated parser SHA-256 assertion before reaching its explicit `FIRST ACCESS TO THE FRESH SONOTACO 2015/2017 ARCHIVES` boundary. Therefore neither fresh archive was requested or inspected.

The original `run_external_validation.py` remains immutable. An execution wrapper may patch exactly two stale parser-provenance string literals in an in-memory/temporary copy:

- 2015: `88bd76001df755ee110d2ce34b7cf3d7d5049840deadbdae397822521aae98b3` -> `3d3d5439ec3e4db50ae79e4ea1ef7df02768be949ee24c5e68b01357b63a3d18`
- 2017: `bed8abe56d647bcb0dd8c5f1177495228ff9c692e26124e9627541e6baabdb3` -> `ee81d66b318ed2fa473ddfcee4c1cea0ef8ba08cba33da47103fd7c53ee625dc`

The wrapper must assert that these are the only two changed source lines before execution. No protocol, detector geometry, proposal generation, scoring, ranking, endpoint, pass gate, parser logic, label handling, blindness rule, or target-access rule may change.
