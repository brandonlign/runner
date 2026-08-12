# OrbitTrace documented CMN interface audit v1 — technical blocker

## Status

`BLOCKED_CMN_DOCUMENTED_INTERFACE_DNS_UNRESOLVED`

This is **not** a scientific/interface-content FAIL and not a CMN method result. The frozen landing-page gate never received an HTTP response because the documented host could not be resolved by DNS on two identical executions from different GitHub-hosted runner regions.

## Frozen provenance

- protocol freeze commit: `526c0599f32ce8d8cf776c7d56b393bab5ceaeb3`
- protocol blob: `eb4fe6e9618aacf0fe2d494c4843a54bb9bf1337`
- implementation freeze commit: `094001ec1e519fada20819c9e652550a0adc8853`
- implementation blob: `bed1676d9dac2779e7e800a14bf112524501877c`
- workflow registration commit: `7219a3ed106fd7a83d860aa6bf52c20a78af8243`

## Exact execution record

Workflow run `31637310066` used the unchanged frozen source in both attempts.

Attempt 1:
- job `94250771209`
- runner region: `westus2`
- transport stopped at DNS resolution with `socket.gaierror: [Errno -2] Name or service not known`
- no HTTP response was received
- artifact `9157457468`
- digest `sha256:977b73be439e436105c5ea16a35e879821320670b2e8d7923460dcd2a17892fc`

Attempt 2, identical frozen rerun:
- job `94250929305`
- runner region: `westus`
- same DNS-resolution error before HTTP
- no HTTP response was received
- artifact `9157475057`
- digest `sha256:a6d7b43f65eefd2beb346ebc8389e27a45c330f2d5cabeecccb180bcd384305d`

Because neither attempt reached HTTP, there is no valid `CMN_DOCUMENTED_INTERFACE_AUDIT_V1` scientific/structural outcome and no candidate file or catalogue row was accessed.

## Interpretation

The independently documented `cmn.rgn.hr` route is currently unusable from the frozen execution environment because the hostname does not resolve. Re-running, changing DNS, guessing neighboring paths, switching schemes outside the preregistered redirect rule, or crawling from this outcome is not an authorized scientific rescue.

CMN's prior zero-data freshness PASS remains intact: this blocker concerns data availability only. A future CMN route would require an independently documented archive/mirror source identified without CMN event-level scientific access and frozen before contact.

## Firewall

- CMN scientific/event-level access: false
- candidate catalogue file downloaded: false
- OrbitTrace target information/events: false
- protected 20°–55° events: inaccessible
- SonotaCo scientific access: false
- MAARSY scientific access: false
- DMS scientific access: false
