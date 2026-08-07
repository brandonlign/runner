# Implementation-only correction 4 — official SNMv3 permanent archive URLs

Status: recorded after a 404 transport failure and before any SonotaCo 2015 or 2017 meteor-record bytes were downloaded.

Retry3 reached the runner's explicit first archive request. The preregistered transport URL `https://sonotaco.jp/doc/SNMv3/015a.zip` returned HTTP 404 immediately. `archive_sources` remained empty and no scientific ranking result was produced.

The official SonotaCo SNMv3 index identifies the permanent historical files on the IAU MDC mirror:

- 2015: `https://www.astro.sk/iaumdcDB/PDA/SNMv3/015a.zip`
- 2017: `https://www.astro.sk/iaumdcDB/PDA/SNMv3/017a.zip`

Resolving the URLs exposed only public archive-index metadata. No event-level meteor coordinates, shower labels, candidate scores, excluded-interval records, or OrbitTrace target information were accessed. The scientific protocol, detector geometry, proposal generation, multiplicity ranking, scaled-K endpoint, power rule, pass gates, parser logic, label ordering, and 20–55 degree exclusion remain unchanged. No gate may be revised using index metadata.

The original preregistered runner remains immutable. A transport wrapper may patch exactly four literals in a temporary copy: the two already-documented parser SHA-256 provenance literals and the two obsolete archive URLs. It must assert that these are the only changed source lines before execution.
