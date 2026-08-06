# SonotaCo 2025 HDBSCAN catalogue result

The checksum-pinned catalogue workflow completed successfully in run `31071589912` and produced artifact `8955917326` (`sha256:82e95052eb75349031341ea600aebf8f74d6842f03c0e47edf7cdea6de471a89`). All source, archive, parser, package-version, parameter, execution, and identical-parameter coverage-audit gates passed.

## Primary published-configuration transfer

This transfers the Peña-Asensio and Ferrari (2025) GEO-vector HDBSCAN configuration to the SonotaCo 2025 benchmark universe after the pre-existing blindness exclusion and published quality filters. It uses the unstandardized six-component GEO vector, `hdbscan==0.8.44`, Euclidean distance, `min_cluster_size=100`, package-default `min_samples`, and `eom` selection.

- 18,939 events;
- 13 reference showers retaining at least 100 quality-filtered events;
- 11 HDBSCAN clusters;
- noise fraction 0.622208;
- NMI 0.747578;
- ARI 0.763809;
- 11/13 showers with matched F1 above 0.5;
- 6/13 above 0.8;
- mean/median matched shower F1 0.704556/0.794074.

## Predeclared all-shower coverage audit

The identical HDBSCAN configuration was also applied without deleting sub-100 reference showers from the blinded quality-filtered universe. This is a coverage diagnostic, not the paper's reference-label-filtered analysis.

- 19,658 events and 66 reference showers;
- 13 clusters;
- NMI 0.705993 and ARI 0.725476;
- mean F1 by quality-filtered annual shower size:
  - 4–9: 0.000000;
  - 10–24: 0.000000;
  - 25–49: 0.030769;
  - 50–99: 0.267677;
  - 100+: 0.707397.

## Interpretation

The result validates HDBSCAN as a strong catalogue method for large annual showers and independently exposes its minimum-size limitation for sparse streams. It therefore complements rather than overturns the episode benchmark: the fixed-4° method addresses sparse four-to-twelve-member recognition, while the published HDBSCAN configuration is designed around clusters of roughly one hundred or more events.

The phrase “full-catalogue coverage audit” refers to all quality-filtered labels retained in the already blinded benchmark universe. The solar-longitude interval 20°–55° remained excluded before label access, so this run did not inspect or score OrbitTrace and is not a blind OrbitTrace rediscovery test.
