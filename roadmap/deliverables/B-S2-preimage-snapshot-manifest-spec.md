# B-S2 · Preimage & snapshot manifest spec

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Specs |
| **Timeline** | 2026-09 → 2027-01 (5 months) |
| **Migration phase** | Phase 1 — Prototypes & Evidence |
| **Milestone alignment** | feeds H\* (2027-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Fix the byte-level formats that make the migration artifact verifiable and reproducible: the
**preimage file format** and the **byte-canonical, PBT-key-sorted, chunked snapshot serialization**,
together with **release-anchored manifest hashes** for per-chunk verification. Byte-canonical
serialization is what lets independent producers emit bit-identical output, and PBT-key ordering is
what turns snapshot ingestion into a sequential bulk-load rather than random inserts.

## Scope — what ships
- **Preimage file byte-level format** — the layout of MPT-key preimages required by (a) self-converters on hash-keyed clients (geth, Nethermind, Besu) and (b) verifiers doing the consensus-anchoring check.
- **Snapshot serialization spec:** byte-canonical (bit-identical across independent producers), sorted in **PBT-key order**, split into chunks sized for a ~100+ GB artifact.
- **Chunk encoding** details — per-chunk framing and the leaf-value encoding within a chunk.
- **Manifest format:** release-anchored manifest hashes giving per-chunk verification, so a downloader can validate each chunk independently against a hash shipped with the client release.
- Reproducibility conformance notes so B-T1 can build golden fixtures against the format.

## Dependencies
- **Upstream (blocks this):** [B-S1](B-S1-eip7748-adaptation.md) — anchor `N` / conversion semantics define what the snapshot and preimages represent.
- **Downstream (this blocks):** [B-C3](B-C3-snapshot-production-pipeline.md), [A-C4](A-C4-snapshot-serving-verification.md), [B-T1](B-T1-conversion-replay-vectors.md).

## Owners / teams
- Migration spec authors (serialization/manifest editors).
- EL client migration leads (snapshot producers and consumers) as format reviewers.
- EF DevOps / distribution (torrent + mirror packaging) for manifest-anchoring review.

## Exit criteria (definition of done)
- [ ] Preimage byte-level format specified and frozen, resolving the §14 open parameter.
- [ ] Snapshot chunk-encoding and byte-canonical serialization specified, resolving the §14 open parameter.
- [ ] Manifest format defined with per-chunk hashes anchored to a client release.
- [ ] Two independent implementations produce a **bit-identical** small-scale snapshot and matching manifest.

## Risks & open questions
- **Preimage byte-level format** and **snapshot chunk encoding** are both open §14 parameters this deliverable must close — see [04-migration.md §Parameters](../../knowledge-base/04-migration.md) and [06-open-questions.md](../../knowledge-base/06-open-questions.md).
- Preimages are essential because the MPT is hash-keyed and cannot be iterated backward into raw keys; extraction at height `E` plus BAL-completion over `(E, N]` gives completeness — the format must carry enough to support that (coordinated with [B-S3](B-S3-bal-replay-spec.md)).
- Chunk sizing trades verification granularity against overhead at ~100+ GB scale; must be validated at scale by [A-C4](A-C4-snapshot-serving-verification.md) and [B-T3](B-T3-dual-check-verification-scale.md).

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
