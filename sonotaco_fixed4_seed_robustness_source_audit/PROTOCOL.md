# SonotaCo fixed-4° calibration-seed robustness source audit

Status: frozen before any meteor archive or score is opened.

## Scientific purpose

The fixed 4° activity-phase scale in PR #113 was the only single fixed phase formulation to clear every original SonotaCo 2025 endpoint, but its k=4 margins were narrow and the broader scale-selection protocol failed. This audit freezes a robustness benchmark of that exact fixed score before any new null panel is generated.

No geometry, scale, event filter, positive episode, threshold, comparator, or scientific endpoint changes. The benchmark uses:

- the exact PR #113 fixed 4° score;
- the exact original calibration/test panel as a reproduction control;
- three independent fresh null panels, each with the unchanged 128 calibration and 64 test negatives per supported bin;
- the exact PR #69/PR #113 positive episodes and complex folds.

The benchmark passes only if the original fixed-4° endpoints reproduce exactly, all fresh panels remain calibrated and discriminative, at least two of three fresh panels clear the complete recall standard, and the fresh-panel median preserves k=4, k=6, and k=8 power.

This is a robustness test, not a new detector candidate or a scale sweep. No panel may be selected after seeing its result.

SonotaCo 2024 and GhostStream remain untouched. A pass authorizes only a separately frozen full SonotaCo 2025 fixed-model development conclusion; it does not authorize opening SonotaCo 2024.

Frozen candidate source SHA-256: `8424f5c1d0a88fc6e2c275437e5d9587eaa1ba71143ab4b4cc87205dcf9b20f0`.
