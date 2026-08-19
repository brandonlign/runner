# OrbitTrace DMS date-derived solar-longitude coverage v1 — binding result

## Verdict

🔴 **INELIGIBLE_DMS_NO_ADEQUATE_CONSECUTIVE_PAIR**

Binding workflow run: `32263460567`

Binding source head: `f79eff566e679d6ce6dafb20d0054f0bed754b1b`

Artifact: `9369191082` (`orbittrace-dms-date-derived-ls-coverage-v1-32263460567`)

Binding result SHA-256: `21fc371aeb2bdc881e3835d02e055aa39b794901d16dc7cf74b02b00a080fecb`.

Only `Yr`, `Mn`, and decimal `Day` were interpreted from DMS data rows. Solar longitude was derived with the preregistered deterministic apparent-geocentric-solar-longitude formula. Radiants, velocities, orbital elements, shower labels, comparators, and OrbitTrace target information were not accessed.

## Coverage result

No DMS year satisfied the frozen coverage gates of at least 80 target-excluded rows, 12 occupied 10° solar-longitude bins, and 3 occupied quadrants.

| year | usable rows | 10° bins | quadrants | eligible |
|---|---:|---:|---:|---|
| 1991 | 5 | 1 | 1 | no |
| 1992 | 0 | 0 | 0 | no |
| 1993 | 118 | 2 | 2 | no |
| 1994 | 0 | 0 | 0 | no |
| 1995 | 305 | 3 | 2 | no |
| 1996 | 165 | 1 | 1 | no |
| 1997 | 71 | 2 | 2 | no |
| 1998 | 237 | 3 | 2 | no |

No consecutive pair was reserved.

## Interpretation

DMS1991-1998 is too seasonally concentrated for the predeclared recurrence/generalization endpoint. This is a **survey-coverage no-go, not a scientific failure of the clustering method**. The coverage gates must not be weakened after this result.
