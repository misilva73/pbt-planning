# B-C3 · Snapshot production pipeline

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2027-02 → 2027-07 (6 months) |
| **Migration phase** | Phase 3 — Migration Machinery |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Turn the converter's output into the distributable migration artifact: a
**~100+ GB, byte-canonical, PBT-key-sorted, chunked snapshot** with a
release-anchored manifest of per-chunk hashes. Byte-canonical serialization means
**independent producers emit a bit-identical artifact**, which is the foundation
for cross-producer agreement and for the dual-check verification any node
(including a fresh one) performs. PBT-key ordering preserves the bulk-load
ingestion property established by the converter.

## Scope — what ships
- A pipeline that consumes converter output and emits the snapshot artifact
  (~100+ GB) in **byte-canonical** serialization → bit-identical across
  independent producers.
- **Chunked** distribution format with a **release-anchored manifest** carrying
  per-chunk hashes for independent per-chunk verification.
- Output sorted in **PBT-key order** so ingestion remains a sequential bulk-load.
- A cross-producer equality harness: two independently run pipelines over the
  same anchor state produce identical chunk hashes and manifest.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section).
  Byte-canonical serialization must erase any per-client DB layout differences so
  the artifact is identical regardless of which client produced it.

## Dependencies
- **Upstream (blocks this):** [B-C1](B-C1-converter-prototype.md) (converter output), [B-S1](B-S1-offline-migration-eip.md) (snapshot + manifest byte-level spec)
- **Downstream (this blocks):** [B-C4](B-C4-production-rehearsals.md), [A-C4](A-C4-snapshot-serving-verification.md), [B-T3](B-T3-dual-check-verification-scale.md)

## Exit criteria (definition of done)
- [ ] Two independent producers emit a **bit-identical** snapshot (identical
      chunk bytes and manifest hashes) from the same anchor state.
- [ ] Snapshot is chunked with a release-anchored manifest; each chunk verifies
      independently against its manifest hash.
- [ ] Artifact is confirmed PBT-key-sorted and ingests as a sequential bulk-load.
- [ ] Manifest hashes are anchored to a specific release build so verifiers know
      which artifact they should reproduce.
- [ ] A corrupted or reordered chunk fails manifest verification.

## Risks & open questions
- **Snapshot chunk encoding is still open (§14)** — chunk boundaries and encoding
  details must be fixed with B-S1 before the format can be frozen.
- **Preimage byte-level format (§14)** likewise feeds the artifact; unresolved
  format details block bit-identical reproduction.
- Any non-determinism in serialization (map ordering, padding, compression
  settings) breaks the bit-identical guarantee and must be eliminated.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [open-questions.md](../../open-questions.md)
