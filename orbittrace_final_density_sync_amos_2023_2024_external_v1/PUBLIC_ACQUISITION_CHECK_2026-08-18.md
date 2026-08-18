# AMOS 2023/2024 public acquisition check — 2026-08-18

## Purpose

Record a zero-data acquisition check for the already-frozen AMOS 2023/2024 final external endpoint. This document does not alter the scientific protocol, authorize a provider request, or access any AMOS event row.

## Findings

### Official AMOS pages

The current Comenius University AMOS pages describe the global network and data-processing program but do not expose a current public bulk download interface for the complete reduced AMOS 2023/2024 multi-station event population required by the frozen endpoint.

Relevant official pages checked:

- https://fmph.uniba.sk/en/microsites/daa/division-of-astronomy-and-astrophysics/research/amos/
- https://fmph.uniba.sk/en/microsites/daa/division-of-astronomy-and-astrophysics/research/amos/amos-video-meteor-network/

An older AMOS network page states that AMOS/SVMN orbits were stored in the EDMOND database.

### Current EDMOND release does not supply the required AMOS 2023/2024 endpoint

The current EDMOND v6.01 page is publicly downloadable through 2024, but its network inventory explicitly lists **SVMN (Slovak Video Meteor Network) as 2007–2016**. Its 2023 and 2024 records therefore cannot be assumed to constitute the complete AMOS 2023/2024 solved multi-station population required by the frozen final-test contract.

Current EDMOND page checked:

- https://meteornews.net/edmond/

EDMOND also applies its own multi-network orbit construction and quality criteria, whereas the frozen AMOS endpoint requires the complete solved AMOS population (including sporadics), exact staged retained-ID handling, and post-freeze AMOS shower associations. Substituting EDMOND would therefore change both survey identity and sample definition.

### IAU MDC is not a direct AMOS 2023/2024 bulk endpoint

The current IAU Meteor Data Center orbit catalogue exposes CAMS, SonotaCo, DMS, GMN and EDMOND video catalogues, but does not list a direct AMOS catalogue matching the frozen staged field contract.

Current MDC page checked:

- https://ceres.ta3.sk/iaumdcdb/

## Conclusion

`NO_PUBLIC_SOURCE_FOUND_THAT_SATISFIES_FROZEN_AMOS_2023_2024_CONTRACT`

The existing staged provider-request draft remains the correct acquisition path if the owner authorizes outreach. Do not silently substitute EDMOND, IAU MDC, or another survey for AMOS after development outcomes are known.

## Firewall state

- provider request sent: false
- AMOS transfer received: false
- AMOS event-level scientific access: false
- AMOS shower-association access: false
- protected OrbitTrace target access: false
- replacement external survey authorized: false
- post-result parameter search: false
