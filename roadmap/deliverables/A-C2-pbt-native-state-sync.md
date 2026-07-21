# A-C2 · PBT-native state sync

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Client implementation |
| **Timeline** | 2027-01 → 2027-06 (5 months) |
| **Migration phase** | Phase 2 — Devnets |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Implement state sync directly over the unified PBT so a fresh node can
reconstruct the tree and verify its root without any MPT round-trip. Sync must
exploit the tree's zone partitioning — the first key byte marks a structural
category — so a node can range-sync one zone (accounts, code overflow, storage)
independently and prove each served range against the canonical root.

## Scope — what ships
- Zone-aware **range sync**: request/serve leaf ranges by contiguous PBT-key
  order within a zone (`0x00` accounts, `0x01` code overflow, `0xFF` storage),
  using the zone boundaries as natural partitioning points.
- Range proofs over the binary tree: boundary branch openings that let a
  receiver verify a served leaf range is complete and correct against the
  target PBT root, using the A-C1 merkelization and canonical-form guarantees.
- Healing / retry logic for ranges that shift under a moving chain head, and
  bulk-load ingestion of received ranges (PBT-key-sorted, so ingestion is a
  sequential append rather than random inserts).
- Wire protocol messages (or extensions) carrying zone-scoped range requests,
  leaf batches, and proof material, integrated with each client's existing
  snap/sync stack.
- Convergence to a verified root that matches A-C3 cross-client agreement.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (+ CL where relevant)

## Dependencies
- **Upstream (blocks this):** [A-C1](A-C1-client-tree-implementations.md) (client tree implementations)
- **Downstream (this blocks):** [A-C4](A-C4-snapshot-serving-verification.md), [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md)

## Exit criteria (definition of done)
- [ ] A fresh node syncs a devnet PBT state from peers and derives a root that
      **agrees cross-client** with the canonical root — no MPT involved.
- [ ] Each served zone range is independently verifiable via a range proof; a
      tampered or incomplete range is rejected.
- [ ] Zones sync independently (a node can complete one zone without touching
      the others) and interrupted sync resumes without restart.
- [ ] Ingestion runs as a sequential bulk-load over PBT-key-sorted ranges.

## Risks & open questions
- Range-proof size depends on PBT's deeper branches and on grinding-resistant
  storage-bucket spread; boundary-opening cost must stay bounded. See
  [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- Serving ranges over a moving head interacts with the not-yet-final expiry /
  deletion semantics (zero-valued leaves are present, not absent).

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
