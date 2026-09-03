# A-C4 · Snapshot serving & verification

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Client implementation |
| **Timeline** | 2027-03 → 2027-09 (6 months) |
| **Migration phase** | Phase 2 — Devnets |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **Partly in flight** (as of 2026-09-02) — geth implements artifact production and full dual-check ingestion; serving/chunked transport and multi-client verification not started |

← [Back to roadmap](../README.md)

## Objective
Give clients the ability to **serve, ingest, and verify** a chunked PBT state
snapshot end-to-end. A node must be able to publish the byte-canonical,
PBT-key-sorted snapshot in chunks, and any node — including a fresh one with no
prior state — must be able to ingest those chunks and authenticate them against
the release-anchored manifest before trusting them. This is the client-side
plumbing the migration snapshot pipeline depends on.

> **Update (2026-09-02).** The *ingestion and verification* half exists in one client:
> `geth bintrie import <snapshot> <preimages> <anchor>`
> ([PR #16](https://github.com/CPerezz/go-ethereum/pull/16), merged 2026-08-17), with
> `--verify-only`, `--force`, `--memory-limit` and `--tmpdir`. Two design points in it are
> worth carrying into this deliverable's spec:
>
> - **The anchor is required and resolved from the node's own header chain** (a block number,
>   or a hash that must be canonical at its height). There is deliberately **no
>   `--anchor-root` flag**: an artifact that vouched for itself would make verification
>   circular. The snapshot header carries only the *claimed* PBT root, which is recomputed.
>   This is the concrete form of "release-anchored manifest" being the wrong root of trust —
>   the same correction already noted in [B-S1](B-S1-offline-migration-eip.md).
> - **The code leg of consensus anchoring is not free.** The MPT commits no code, so every
>   distinct bytecode is reassembled from its chunk leaves (absent chunks reading as 31 zero
>   bytes), truncated to `code_size`, required to keccak to its `code_hash`, then
>   **re-chunked and compared byte for byte** against the artifact's leaves — which is what
>   pins each chunk's push-data offset, padding and placement, none of which the hash alone
>   can see.
>
> Reported cost on the converter's fixture (70k accounts / 140k slots / 5.2k codes): import
> 2.03 s vs convert 5.05 s, so **consuming costs about two-fifths of producing**, with
> artifacts at 29.4 MB against a 114.7 MB datadir. Page-cache-resident, so compute-only.
>
> **Still missing, and it is most of this deliverable:** serving (nothing emits chunks for
> transport), resumable bulk-load markers, composition with [A-C2](A-C2-pbt-native-state-sync.md)
> range sync, and any second implementation — so "a second independent producer reproduces it
> bit-for-bit" remains untested.

## Scope — what ships
- Snapshot **serving**: emit the ~100+ GB artifact as manifest-described chunks,
  byte-canonical (bit-identical across independent producers) and sorted in
  PBT-key order.
- Snapshot **ingestion**: sequential bulk-load of chunks into the client's PBT
  DB layout (append in key order, not random insert), with resumability markers.
- **Verification**: internal PBT-consistency rebuild (rebuild tree from leaves →
  derive keys → hash bottom-up → check the *claimed* PBT root, never trust it) plus
  transport-level integrity on arrival. Note the **manifest is not the root of trust** —
  EIP-8347 makes the chunk index optional and non-normative and anchors verification to
  `ANCHOR_BLOCK`'s `stateRoot` from the node's own header chain; a release-pinned `pbtRoot`
  is optional hardening only, and cannot cover after-release re-anchor snapshots. See
  [B-S1](B-S1-offline-migration-eip.md).
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
- [ ] A fresh node ingests the chunks, verifies transport integrity on arrival,
      rebuilds the PBT, and confirms the claimed root against an anchor taken from
      **its own header chain** — rejecting any tampered chunk and any artifact that
      vouches for itself.
- [ ] Ingestion is a resumable sequential bulk-load over PBT-key-sorted chunks.
- [ ] Snapshot ingestion composes with A-C2 range sync for the chain tail.

## Risks & open questions
- Snapshot **transport chunking** remains an open §14 parameter and is left to the
  distribution layer by EIP-8347; the **preimage format** is specified but moved on
  2026-08-20 to fixed-width, hashed-key-ordered records, and the one existing implementation
  still writes the old layout. Serving/verification code must track that, not a manifest
  spec. See [open-questions.md](../../open-questions.md).
- Consensus-anchoring (rehash under MPT schema vs block `N` `stateRoot`) is a
  migration-context check owned by the B thread; A-C4 covers internal
  PBT-consistency and manifest authentication of the artifact itself.

## References
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [open-questions.md](../../open-questions.md)
