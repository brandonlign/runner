# MSSWG readme-only schema audit v1 — result

**Classification: NEUTRAL / PREACCESS BLOCKED. MSSWG event catalogue remains untouched.**

Binding attempt:

- workflow run `31832431383`;
- job `94871013331`;
- exact frozen readme target `http://www.imo.net/files/data/msswg/readme`;
- one application-level GET;
- returned HTTP `404`;
- no automatic redirect to a usable documentation object;
- no readme bytes preserved because the frozen fetch failed closed on non-200;
- no `msswg.txt` request;
- no MSSWG event/scientific value access.

The attempt followed a clean zero-data freshness PASS (`31832150805`, artifact `9231082708`) and a clean official-interface structure PASS (`31832289541`, artifact `9231133489`). The latter discovered exactly one visible `readme` link and exactly one `msswg.txt` link on the official IMO video-data page, and followed neither.

## Binding consequence

The exact documented readme route is blocked by link rot under the frozen protocol.

Do **not** rescue this result by:

- changing `http` to `https` after seeing the 404;
- guessing `readme.txt`, `README`, or neighboring paths;
- crawling the parent directory;
- jumping directly to `msswg.txt` without the required readme/schema compatibility gate;
- searching mirrors based on the failed target.

Verdict:

`BLOCKED_MSSWG_README_SCHEMA_AUDIT_EXACT_DOCUMENTED_LINK_404`

This is neither evidence for nor against recurrent-EOM HDBSCAN. MSSWG remains scientifically fresh at the catalogue/event level but is **not authorized for detector execution** through this route.

## Firewall

- `msswg_catalogue_access=false`
- `msswg_event_value_access=false`
- `msswg_readme_successful_access=false`
- `target_information_access=false`
- `target_region_events_accessed=false`
- `maarsy_scientific_access=false`
- `dms_scientific_access=false`
