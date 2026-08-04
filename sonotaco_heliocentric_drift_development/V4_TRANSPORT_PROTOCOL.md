# SonotaCo heliocentric drift development v4 transport repair

PR #121's first attempt showed that the manually line-wrapped payload was checksum-consistent but gzip-corrupted. The frozen source was re-encoded locally as one continuous Base64 line.

The only permitted changes are:

- replace the encoded transport file with the one-line encoding of the already frozen v2 source;
- set the outer file SHA-256 to `34e23118534eca95864d1bee123707316e896bba5169e76d3d5c777bf2d7cb5a`.

The decoded source must still match `10e87a4ada2eaceb5a8852642f786ce3e8e3978ac490844104c346532e41508c`. No decoded source byte or scientific setting changes. SonotaCo 2024 and GhostStream remain untouched.
