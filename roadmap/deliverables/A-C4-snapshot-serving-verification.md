# A-C4 · Snapshot serving & verification

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Client implementation |
| **Timeline** | 2027-03 → 2027-09 (6 months) |
| **Migration phase** | Phase 2 — Devnets |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Give clients the ability to **serve, ingest, and verify** a chunked PBT state
snapshot end-to-end. A node must be able to publish the byte-canonical,
PBT-key-sorted snapshot in chunks, and any node — including a fresh one with no
prior state — must be able to ingest those chunks and authenticate them against
the release-anchored manifest before trusting them. This is the client-side
plumbing the migration snapshot pipeline depends on.

## Scope — what ships
- Snapshot **serving**: emit the ~100+ GB artifact as manifest-described chunks,
  byte-canonical (bit-identical across independent producers) and sorted in
  PBT-key order.
- Snapshot **ingestion**: sequential bulk-load of chunks into the client's PBT
  DB layout (append in key order, not random insert), with resumability markers.
- **Manifest verification**: per-chunk hash checks against the release-anchored
  manifest (per the B-S1 manifest spec), plus internal PBT-consistency rebuild
  (rebuild tree from leaves → derive keys → hash bottom-up → check claimed PBT
  root).
- Integration with A-C2 range sync so a node can mix snapshot ingestion with
  peer range-sync for the tail.
- Devnet exercise: one client serves, others ingest and independently verify to
  the same root.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (+ CL where relevant)

## Dependencies
- **Upstream (blocks this):** [A-C2](A-C2-pbt-native-state-sync.md) (PBT-native state sync), [B-S1](B-S1-offline-migration-eip.md) (snapshot manifest spec)
- **Downstream (this blocks):** [B-C3](B-C3-snapshot-production-pipeline.md)

## Exit criteria (definition of done)
- [ ] A node serves a chunked snapshot that a second, independent producer
      reproduces **bit-for-bit** (byte-canonical).
- [ ] A fresh node ingests the chunks, verifies every chunk against the
      manifest, rebuilds the PBT, and confirms the claimed root — rejecting any
      tampered chunk.
- [ ] Ingestion is a resumable sequential bulk-load over PBT-key-sorted chunks.
- [ ] Snapshot ingestion composes with A-C2 range sync for the chain tail.

## Risks & open questions
- Snapshot chunk encoding and the preimage byte-level format are still open
  parameters (§14); serving/verification code must track the B-S1 manifest spec
  as it settles. See [open-questions.md](../../open-questions.md).
- Consensus-anchoring (rehash under MPT schema vs block `N` `stateRoot`) is a
  migration-context check owned by the B thread; A-C4 covers internal
  PBT-consistency and manifest authentication of the artifact itself.

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [open-questions.md](../../open-questions.md)
