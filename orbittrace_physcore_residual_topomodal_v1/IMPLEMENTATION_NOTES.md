# Engineering implementation notes

This directory implements the already-frozen `PROTOCOL.md`. Scientific choices remain defined exclusively by that protocol.

The frozen TopoModal source is vendored byte-for-byte from Git blob `752df8212ce601227f6e9170b0fe994ba06b515d`; implementation work must not edit that blob. Any post-execution repair is limited to execution plumbing and must leave the protocol, candidate construction, ordering, activation gates, evaluator semantics, and source identities unchanged.
