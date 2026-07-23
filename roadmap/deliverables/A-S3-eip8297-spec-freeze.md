# A-S3 · EIP-8297 Spec Freeze

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Specs |
| **Timeline** | 2027-01 → 2027-03 (3 months) |
| **Migration phase** | Phase 2-3 |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Freeze the final EIP-8297 as the H\* Considered-for-Inclusion (CFI) spec: keys, node types, and hash function `H` all fixed, with no remaining open structural parameters. Gas cost constants are out of scope for this freeze and are owned entirely by [A-S2](A-S2-gas-cost-recalibration.md). The freeze gives client teams a **stationary target** to build against through the conformance, devnet, and migration rehearsals that run toward fork S. This is the H\* milestone deliverable for the Trie Design thread.

## Scope — what ships
- A frozen EIP-8297 text in which every previously-open parameter is pinned:
  - **Keys** — variable-length, prefix-free; per-zone fixed lengths (accounts/code 34 bytes, storage 66 bytes); `MAX_KEY_LENGTH = 8192`; first-byte zones (`0x00`/`0x01`/`0xFF`, `0x02`–`0xFE` reserved).
  - **Node types** — `LeafNode` (complete key + value) and `BranchNode` (compressed bit prefix + two children); tagged merkelization (`LEAF_TAG`/`BRANCH_TAG`).
  - **Hash `H`** — the function decided by the [hash-function dependency](../README.md) (external, due end 2026), fixed for both merkelization and `key_hash` (including Poseidon2 field encoding if selected).
- Gas cost constants are **explicitly out of scope** for this freeze: they are owned entirely by [A-S2](A-S2-gas-cost-recalibration.md) and follow the decoupled gas-focused fork track, consistent with PBT-native gas being off the critical path to the swap.
- CFI status secured on the H\* fork agenda (coordinated via [A-O1](A-O1-tree-spec-socialization.md)).
- A change-control statement: post-freeze edits require re-opening only through explicit process, so rehearsals target a stable spec.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) (base design) and the [hash-function dependency](../README.md) (hash `H`, external, due end 2026) — both must be resolved before freeze. Gas cost recalibration ([A-S2](A-S2-gas-cost-recalibration.md)) is **decoupled** and is **not** a freeze blocker; gas constants are out of scope for this freeze and owned entirely by A-S2.
- **Downstream (this blocks):** the migration thread's rehearsals and devnets rely on a frozen spec — e.g. [A-T3](A-T3-pbt-genesis-conformance-sync-tests.md), [A-C3](A-C3-multiclient-pbt-genesis-devnets.md), [B-T2](B-T2-full-cycle-devnet-swap.md), and ultimately the mainnet window [B-C6](B-C6-mainnet-window.md).

## Owners / teams
- EIP-8297 authors (spec editors) — produce the frozen text.
- EL client teams — confirm implementability against the frozen parameters.
- ACDE/ACDC coordination via [A-O1](A-O1-tree-spec-socialization.md) — secures CFI/H\* scheduling.

## Exit criteria (definition of done)
- [ ] Keys, node types, and hash `H` all fixed in the EIP text with no `TBD`/pending markers; gas cost constants out of scope for this freeze (owned entirely by [A-S2](A-S2-gas-cost-recalibration.md)).
- [ ] Poseidon2 field encoding (if applicable) included and final.
- [ ] EIP-8297 accepted as CFI on the H\* (2027-06) fork agenda.
- [ ] Client teams sign off that the frozen spec is a stationary target for rehearsals.
- [ ] Change-control process for any post-freeze amendment documented.

## Risks & open questions
- Freeze depends on the [hash-function dependency](../README.md) (hash `H`, the dominant open parameter) resolving by end 2026; slippage there pushes the freeze. Gas cost recalibration ([A-S2](A-S2-gas-cost-recalibration.md)) is deliberately decoupled and does **not** block the freeze — gas constants are out of scope for the freeze and handled entirely in A-S2. See [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- State-expiry / resurrection mechanics are deferred to a separate EIP and are explicitly **out of scope** for this freeze; the frozen spec must not embed assumptions that block a later expiry EIP (e.g. reserved zones, reference counting for shared code).
- Diagram and rendered spec-site content must be brought in line with the frozen design so the CFI artifact is internally consistent (the old stem-node diagram must already be redrawn per [A-S1](A-S1-eip8297-spec-convergence.md)).

## References
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md)
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md)
- [knowledge-base/05-design-evolution.md](../../knowledge-base/05-design-evolution.md)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md)
- EIP-8297 (requires EIP-4762, EIP-7612); H\* CFI process.
