# B-C2 · BAL-replay engine

| | |
|---|---|
| **Thread** | B · Migration |
| **Workstream** | Client implementation |
| **Timeline** | 2027-01 → 2027-05 (5 months) |
| **Migration phase** | Phase 3 — Migration Machinery |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | **In flight, ~5 months early** (as of 2026-09-17) — geth's migration follower replays BALs onto the shadow tree, backfills over `eth/71`, and drives the swap. **Still the only BAL-replay implementation**: the three clients that joined the migration devnet in September migrate by other means (Erigon folds both commitment domains, Besu swaps the trie per header, Nethermind mirrors flat state), so the devnet going multi-client does *not* make this deliverable multi-client. Still exercised on trivial state. |

← [Back to roadmap](../README.md)

## Objective
Build the engine that catches a converted snapshot up from anchor block `N` to
the chain tip **without re-execution**, by applying per-block state writes drawn
from **Block-Level Access Lists (EIP-7928)**. Replay applies translation rules
per entry type (balance/nonce changes, storage writes, code deployments) directly
onto the PBT. Batching bounds replay cost while keeping convergence comfortably
**below the steady-state block-production rate**, so a node can close the gap to
tip and stay there.

> **Update (2026-09-02).** geth's migration follower
> ([PR #31](https://github.com/CPerezz/go-ethereum/pull/31), merged 2026-08-21) implements
> this deliverable plus a good deal of what [B-C6](B-C6-mainnet-window.md) and
> [B-C7](B-C7-swap-fork-s-aftermath.md) assume. The node holds **both trees in one chaindata
> database**; a follower replays block access lists onto whichever tree execution is not
> committing; the header state root **swaps source at `binaryTrieTime`** with the merkle side
> maintained until a post-fork block finalizes (or a configured `MigrationWindowBlocks`
> elapses). Specifically:
>
> - Catch-up starts either from genesis-seeded state or from an anchor imported by
>   `geth bintrie import`, with `--force` replacing a stale position.
> - Replay batches through `bal.Fold` outside the 128-block tracking window, and **every
>   list is proven against the header commitment before it is applied**.
> - Missing access lists are **backfilled over `eth/71`**, with forging peers dropped and
>   unavailable ones rotated past.
> - `debug_shadowStateRoot` / `debug_shadowRoots` expose the sidecar feed and
>   `debug_migrationProgress` reports per direction; shutdown journals each handle at the
>   newest root it holds, so reboots resume both directions from their cursors.
> - `TestFullMigrationLifecycle` drives empty state through replay, swap, a live window, a
>   mid-window reboot and the finality close.
>
> A follow-up ([PR #33](https://github.com/CPerezz/go-ethereum/pull/33), 2026-09-01) fixed a
> genuine wedge: a reorg whose branches each cross activation independently made insertion
> ask the follower for the shadow root of a not-yet-canonical block, and the height-bounded
> forward walk replayed nothing — hanging 30 s on the chain mutex and then failing the
> import. Resolved by walking back through parent hashes to the nearest replayed ancestor.
> This is the [fork-boundary reorg question](../../open-questions.md#reorg-behavior-around-the-swap)
> showing up as a real bug, answered in one client's code and **still unspecified**.
>
> **Caveats.** Single-client; the migration devnet that exercises it passed its M1 gate on
> **empty state** (2026-08-27), so nothing here speaks to convergence rate against real
> mainnet block content — which is this deliverable's central exit criterion.

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
- **Upstream (blocks this):** [B-S1](B-S1-offline-migration-eip.md) (BAL-replay translation rules on EIP-7928)
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
  rehearsals (B-C4) can fully validate. Nothing measured so far bears on it: the existing
  implementation's lifecycle test and the devnet's M1 gate both run on **empty state**.
- **Reorg handling at the activation boundary is being settled in code rather than in spec.**
  geth has now shipped an answer to a wedge that the EIP does not describe (PR #33 above).
  Every other client will meet the same case and may answer differently — which is the
  correlated-divergence shape a readiness gate is least able to see. Pull the procedure into
  [B-S1](B-S1-offline-migration-eip.md) before a second implementation starts.
- **BAL-replay's account-deletion trigger now has an explicit dependency.** EIP-8347 added
  `EIP-7523` to its `requires` on 2026-08-25 precisely because the
  `nonce == 0 ∧ balance == 0 ∧ code_size == 0` rule is only exact in both directions if no
  empty account survives in the MPT. Replay implementations must not re-derive that trigger
  from first principles.

## References
- [knowledge-base/04-migration.md](../../knowledge-base/04-migration.md)
- [knowledge-base/01-overview.md](../../knowledge-base/01-overview.md)
- [open-questions.md](../../open-questions.md)
