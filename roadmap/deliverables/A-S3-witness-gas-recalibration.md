# A-S3 · Witness Gas Recalibration

| | |
|---|---|
| **Thread** | A · Trie Design |
| **Workstream** | Specs |
| **Timeline** | 2026-10 → 2027-04 (7 months) |
| **Migration phase** | Phase 1 |
| **Milestone alignment** | feeds H\* (2027-06) / fork S = I\* (2028-06) |
| **Status** | Not started (as of 2026-07) |

← [Back to roadmap](../README.md)

## Objective
Recalibrate the EIP-4762 access-event gas schedule for PBT's tree geometry and specify content-addressed-code access accounting. EIP-4762 prices a witness branch at `WITNESS_BRANCH_COST = 1900`, a value calibrated for **shallow Verkle branches**; PBT is an arity-2 binary tree whose branches are **deeper**, so charging Verkle-era constants would misprice witnesses. This deliverable produces PBT-appropriate access-event gas constants and the tree-key–based accounting rules that the frozen spec depends on.

## Scope — what ships
- Recalibrated EIP-4762 access-event gas constants for PBT's depth profile — in particular a PBT value for `WITNESS_BRANCH_COST` (and related witness constants) replacing the Verkle-calibrated `1900`.
- Spec for **content-addressed code access accounting**: overflow code chunks (chunk_id ≥ 128, in `CODE_ZONE`) are shared between contracts with identical bytecode, so their access events MUST be keyed by the `(zone, tree_position, sub-index)` **tree-key**, **not** by `(address, chunk)`. A shared chunk is charged once per block regardless of which contract triggers it, and the witness carries a single copy. Header chunks (0..127, in the account stem) remain per-account.
- Documentation of how the recalibration was derived (depth distribution of PBT branches vs Verkle), so the constants are defensible at freeze.

## Dependencies
- **Upstream (blocks this):** [A-S1](A-S1-eip8297-spec-convergence.md) (stable key scheme and node types). Informed by [A-T4](A-T4-hardware-matrix-benchmarks.md) benchmarks (state-op and proof measurements that ground the depth/cost profile).
- **Downstream (this blocks):** [A-S4](A-S4-eip8297-spec-freeze.md) (gas constants must be fixed to freeze the spec).

## Owners / teams
- EIP-8297 authors and EIP-4762 maintainers (access-event framework).
- EL client teams — provide branch-depth distributions and witness-size measurements from prototypes ([A-C1](A-C1-client-tree-implementations.md)) and the hardware matrix ([A-T4](A-T4-hardware-matrix-benchmarks.md)).

## Exit criteria (definition of done)
- [ ] PBT-calibrated witness gas constants (incl. `WITNESS_BRANCH_COST`) proposed with supporting depth/cost analysis.
- [ ] Content-addressed code access spec'd: overflow chunks keyed by tree-key, charged once per block; header chunks per-account.
- [ ] Constants validated against representative worst-case and typical-block witness sizes.
- [ ] Values handed to [A-S4](A-S4-eip8297-spec-freeze.md) for inclusion in the frozen H\* spec.

## Risks & open questions
- **The recalibrated values are not yet fixed** in the current draft — this deliverable is what fixes them. Until then, gas constants in the spec are marked pending. See [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md) (Access events) and [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- Circular timing with benchmarks: good calibration wants [A-T4](A-T4-hardware-matrix-benchmarks.md) data (2027-07→2027-12), but freeze [A-S4](A-S4-eip8297-spec-freeze.md) targets H\* (2027-06); this deliverable must land defensible constants from early prototype data, with the hardware matrix serving as later confirmation rather than a prerequisite.
- Branch depth depends on grinding resistance and prefix compression; mispricing could under-charge grinded deep subtrees. See the "Grinding" note in [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md).
- Reference-counting for shared code leaves (state-expiry interaction) is deferred to a separate EIP but touches access accounting assumptions.

## References
- [knowledge-base/03-key-derivation.md](../../knowledge-base/03-key-derivation.md) (Access events / gas)
- [knowledge-base/02-tree-structure.md](../../knowledge-base/02-tree-structure.md) (arity-2 branch depth)
- [knowledge-base/06-open-questions.md](../../knowledge-base/06-open-questions.md) (witness gas recalibration; grinding)
- EIP-4762 (access events); EIP-8297.
