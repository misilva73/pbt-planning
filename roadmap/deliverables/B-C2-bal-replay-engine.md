# B-C2 · BAL-replay engine

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2027-01 → 2027-05 (5 months) |
| **Migration phase** | Phase 3 — Migration Machinery |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Build the engine that catches a converted snapshot up from anchor block `N` to
the chain tip **without re-execution**, by applying per-block state writes drawn
from **Block-Level Access Lists (EIP-7928)**. Replay applies translation rules
per entry type (balance/nonce changes, storage writes, code deployments) directly
onto the PBT. Batching bounds replay cost while keeping convergence comfortably
**below the steady-state block-production rate**, so a node can close the gap to
tip and stay there.

## Scope — what ships
- A BAL-replay engine that ingests EIP-7928 BALs and applies per-block state
  writes onto a PBT built from a snapshot, with **no EVM re-execution**.
- Translation rules per entry type: balance/nonce updates, storage writes, and
  code deployments. **Zero-writes delete leaves** (zeros encoded as absence in
  the migration context); **account deletion needs no special BAL marker**.
- Batching that bounds per-cycle replay cost and demonstrably converges faster
  than blocks are produced.
- **BAL-completion over `(E, N]`**: when preimages are extracted at an earlier
  height `E` than the anchor `N`, replay over that interval restores completeness
  of the converted state.

## Client coverage
- EL: geth, Nethermind, Besu, Reth, Erigon (note hash-keyed vs raw-keyed DB
  differences where relevant — see 04-migration.md preimages section). Replay
  writes into each client's PBT store; hash-keyed vs raw-keyed layouts must not
  change the resulting PBT root.

## Dependencies
- **Upstream (blocks this):** [B-S3](B-S3-bal-replay-spec.md) (BAL-replay translation rules on EIP-7928)
- **Downstream (this blocks):** [B-C4](B-C4-production-rehearsals.md), [B-C6](B-C6-mainnet-window.md)

## Exit criteria (definition of done)
- [ ] Replay applies BALs from `N` to tip and reaches a PBT root identical to a
      from-scratch conversion at the same height.
- [ ] Convergence rate is measured to be below block-production rate under
      realistic batching (the engine catches up and holds at tip).
- [ ] Zero-value writes remove the corresponding leaf; account deletion is
      handled with no special BAL marker.
- [ ] BAL-completion over `(E, N]` produces a state that matches a converter run
      anchored directly at `N`.
- [ ] All three write categories (balance/nonce, storage, code) are covered by
      replay vectors (B-T1) and cross-checked across clients.

## Risks & open questions
- **BAL availability & correctness upstream.** EIP-7928 ships in **Glamsterdam
  (≈ 2026-09)**, so BAL is assumed mainnet-live before this work; BALs must still
  be complete and correct per block — a missing or malformed BAL breaks
  no-re-execution replay. The `(E, N]` completion path is the mitigation for
  preimage/anchor height mismatches.
- Batch sizing is a performance/latency trade-off that only mainnet-scale
  rehearsals (B-C4) can fully validate.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
