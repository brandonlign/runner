# GFO 2022/2023 capacity audit v1

PRE-DATA FREEZE. Fixed years: 2022 and 2023; no alternate year pair after outcome.

Purpose: necessary-capacity test only for unchanged OrbitTrace fixed4 architecture. Official GFO L5 public summary catalogue/interface only. Read only row existence and `event_codename` or `datetime` needed to count annual rows. Do not read/emit solar longitude, radiant, velocity, orbit, shower label, protected-region membership, or other scientific values.

Frozen necessary gate: the unchanged calibration uses 128 episodes per supported 10-degree bin; 36 annual bins implies 4,608 rows/year even before blind exclusion/applicability losses. PASS only if N2022>=4608 AND N2023>=4608. PASS authorizes only a separately frozen bin/applicability audit. FAIL closes GFO 2022/2023 for this unchanged architecture; do not lower the floor or switch years.

Use only an official `gfo.rocks` or `dfn.gfo.rocks` interface linked from official GFO data pages; no guessed-path catalogue crawl. No OrbitTrace target info/events, SonotaCo science, protected 20-55 scientific values, MAARSY or DMS access. No method/power-floor change.