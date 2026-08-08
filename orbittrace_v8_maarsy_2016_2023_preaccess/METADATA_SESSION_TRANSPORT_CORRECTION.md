# MAARSY metadata export anonymous-session transport correction

Frozen after Stage-0B execution run `31231642458` failed on the first `rel=describedby` request with HTTP 401 and before any metadata export body, dataset-content file, or event value was parsed.

The public DOI landing page had already returned an anonymous `RADAR_SESSION_ID` cookie during successful Stage-0A. This correction changes transport only:

1. request the already-frozen public landing page `https://www.radar-service.eu/radar/en/dataset/yk29t2gu0h4jhkjg` and save its anonymous cookies;
2. request the same three already-frozen `rel=describedby` endpoints using that cookie jar;
3. do not request the `rel=item` dataset archive URL;
4. do not use credentials, login, API tokens, or any private resource.

All metadata parsing guards, no-event-access restrictions, v8 scientific rules, power floors, and OrbitTrace/GMN firewalls remain unchanged.