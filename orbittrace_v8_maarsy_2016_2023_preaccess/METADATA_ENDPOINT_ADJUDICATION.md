# MAARSY metadata endpoint availability adjudication

Frozen after anonymous-session retry run `31231715776` and before any dataset-content request.

That run established the public anonymous RADAR session successfully and downloaded the frozen `exportradarmetadata` description (`2391` bytes). It then stopped because the advertised `exportrocrate` URL returned HTTP 404. No metadata body was parsed, no dataset archive was requested, and no event/scientific value was accessed.

The failure is endpoint availability, not a scientific or interface result. This correction freezes independent handling of the three already-advertised `rel=describedby` endpoints:

- `exportradarmetadata`: HTTP 200 is required;
- `exportJsonld`: request and record its HTTP status; parse only if 200;
- `exportrocrate`: request and record its HTTP status; parse only if 200; a 404 is an allowed metadata-export absence and must not abort analysis of the other public descriptions.

The actual `rel=item` dataset archive remains forbidden. No new endpoint may be invented from response content. No credentials or authenticated account may be used.

All parsing remains structural/metadata-only. v8, power floors, target firewall, and GMN Stage A/Stage B block remain unchanged.