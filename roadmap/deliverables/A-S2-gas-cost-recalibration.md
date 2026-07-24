# A-S2 · Gas Cost Recalibration

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Specs |
| **Timeline** | 2028-01 → 2028-03 (3 months) |
| **Migration phase** | Deferred — post-benchmark (PBT-native gas decoupled from the swap) |
| **Milestone alignment** | decoupled from H\*/I\*; feeds a later gas-focused fork |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Recalibrate the EIP-4762 access-event gas schedule for PBT's tree geometry and specify content-addressed-code access accounting. EIP-4762 prices a witness branch at `WITNESS_BRANCH_COST = 1900`, a value calibrated for **shallow Verkle branches**; PBT is an arity-2 binary tree whose branches are **deeper**, so charging Verkle-era constants would misprice witnesses. This deliverable produces PBT-appropriate access-event gas constants and the tree-key–based accounting rules that the frozen spec depends on.

## Scope — what ships
- Recalibrated EIP-4762 access-event gas constants for PBT's depth profile — in particular a PBT value for `WITNESS_BRANCH_COST` (and related witness constants) replacing the Verkle-calibrated `1900`.
- Spec for **content-addressed code access accounting**: overflow code chunks (chunk_id ≥ 128, in `CODE_ZONE`) are shared between contracts with identical bytecode, so their access events MUST be keyed by the `(zone, tree_position, sub-index)` **tree-key**, **not** by `(address, chunk)`. A shared chunk is charged once per block regardless of which contract triggers it, and the witness carries a single copy. Header chunks (0..127, in the account stem) remain per-account.
- Documentation of how the recalibration was derived (depth distribution of PBT branches vs Verkle), so the constants are defensible at freeze.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) (stable key scheme and node types) and [A-T4](A-T4-hardware-matrix-benchmarks.md) hardware-matrix benchmarks — this deliverable is **deferred until the benchmark data lands** (2027-12), so the recalibration is grounded on measured state-op and proof costs rather than early estimates.
- **Downstream (this blocks):** a **later gas-focused fork**. This does **not** block the [A-S3](A-S3-eip8297-spec-freeze.md) spec freeze (which fixes only the structural parameters — keys, node types, hash `H`); gas cost constants are out of scope for the freeze and owned here, and PBT-native gas is deliberately decoupled from the swap.

## Owners / teams
- EIP-8297 authors and EIP-4762 maintainers (access-event framework).
- EL client teams — provide branch-depth distributions and witness-size measurements from prototypes ([A-C1](A-C1-client-tree-implementations.md)) and the hardware matrix ([A-T4](A-T4-hardware-matrix-benchmarks.md)).

## Exit criteria (definition of done)
- [ ] PBT-calibrated witness gas constants (incl. `WITNESS_BRANCH_COST`) proposed with supporting depth/cost analysis.
- [ ] Content-addressed code access spec'd: overflow chunks keyed by tree-key, charged once per block; header chunks per-account.
- [ ] Constants validated against representative worst-case and typical-block witness sizes.
- [ ] Recalibrated values packaged for a later gas-focused fork (superseding the provisional constants in place through the swap).

## Risks & open questions
- **The recalibrated values are not yet fixed** in the current draft — this deliverable is what fixes them. Until then, gas constants in the spec are marked pending. See [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md) (Access events) and [open-questions.md](../../open-questions.md).
- Because **provisional** gas constants are in place through the swap while this recalibration waits on [A-T4](A-T4-hardware-matrix-benchmarks.md) data (2027-07→2027-12), the network runs on provisional gas pricing until the later gas-focused fork adopts the recalibrated values; the provisional constants must therefore be conservative enough to be safe in the interim.
- Branch depth depends on grinding resistance and prefix compression; mispricing could under-charge grinded deep subtrees. See the "Grinding" note in [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- Reference-counting for shared code leaves (state-expiry interaction) is deferred to a separate EIP but touches access accounting assumptions.

## References
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md) (Access events / gas)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md) (arity-2 branch depth)
- [open-questions.md](../../open-questions.md) (witness gas recalibration)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md) (grinding note)
- EIP-4762 (access events); EIP-8297.
